let detectedPins = [];

const scanBtn = document.getElementById('scanBtn');
const scanDepthSelect = document.getElementById('scanDepthSelect');
const downloadBtn = document.getElementById('downloadBtn');
const pinCountBadge = document.getElementById('pinCountBadge');
const selectionSummary = document.getElementById('selectionSummary');
const selectAllCheckbox = document.getElementById('selectAllCheckbox');
const gallery = document.getElementById('gallery');
const subfolderInput = document.getElementById('subfolderInput');
const progressContainer = document.getElementById('progressContainer');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');

// Load saved subfolder preference
try {
  const savedFolder = localStorage.getItem('pinterest_wallpaper_subfolder');
  if (savedFolder) subfolderInput.value = savedFolder;
} catch (e) {}

subfolderInput.addEventListener('change', () => {
  try {
    localStorage.setItem('pinterest_wallpaper_subfolder', subfolderInput.value.trim());
  } catch (e) {}
});

scanBtn.addEventListener('click', () => {
  runContinuousScraper();
});

selectAllCheckbox.addEventListener('change', (e) => {
  const checked = e.target.checked;
  const checkboxes = gallery.querySelectorAll('input[type="checkbox"]');
  checkboxes.forEach(cb => {
    cb.checked = checked;
  });
  updateSelectionCount();
});

downloadBtn.addEventListener('click', () => {
  startDownloadZip();
});

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function runContinuousScraper() {
  const tab = await getActiveTab();
  if (!tab || !tab.url || !tab.url.includes('pinterest.')) {
    alert('Please open a Pinterest board or feed in this tab first!');
    return;
  }

  const targetOption = scanDepthSelect.value;
  scanBtn.disabled = true;
  scanDepthSelect.disabled = true;
  scanBtn.textContent = '⏳ Scanning & Scrolling...';

  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: continuousScraperInPage,
      args: [targetOption]
    });

    if (results && results[0] && results[0].result) {
      detectedPins = results[0].result;
      renderGallery(detectedPins);
    }
  } catch (err) {
    console.error('Error during scraping:', err);
    alert('Failed to scan page: ' + err.message);
  } finally {
    scanBtn.disabled = false;
    scanDepthSelect.disabled = false;
    scanBtn.textContent = '🚀 Start Scan & Collect';
  }
}

// Injected into the Pinterest webpage to scroll and accumulate pins continuously
async function continuousScraperInPage(targetOption) {
  const pinMap = new Map();

  function scanCurrentDOM() {
    const images = Array.from(document.querySelectorAll('img'));
    for (const img of images) {
      let src = img.currentSrc || img.src;

      if (img.srcset) {
        const candidates = img.srcset.split(',').map(s => s.trim().split(' ')[0]);
        if (candidates.length > 0) {
          const best = candidates[candidates.length - 1];
          if (best && best.includes('i.pinimg.com')) {
            src = best;
          }
        }
      }

      if (!src || !src.includes('i.pinimg.com')) continue;

      if (src.includes('/75x75_RS/') || src.includes('/30x30/') || src.includes('/60x60/') || src.includes('/user/')) {
        continue;
      }

      const originalUrl = src.replace(/\/(236x|474x|564x|736x)\//, '/originals/');
      const previewUrl = src;

      const parts = originalUrl.split('/');
      let filename = parts[parts.length - 1].split('?')[0];

      if (filename && filename.match(/\.(jpg|jpeg|png|webp)$/i)) {
        if (!pinMap.has(filename)) {
          pinMap.set(filename, {
            filename: filename,
            originalUrl: originalUrl,
            previewUrl: previewUrl
          });
        }
      }
    }
  }

  scanCurrentDOM();

  if (targetOption === 'current') {
    return Array.from(pinMap.values());
  }

  const targetCount = targetOption === 'all' ? 500 : parseInt(targetOption, 10);
  let scrollStep = 550;
  let maxAttempts = targetOption === 'all' ? 120 : Math.ceil(targetCount / 3) + 10;
  let stagnantCount = 0;
  let lastSize = pinMap.size;

  for (let i = 0; i < maxAttempts; i++) {
    if (pinMap.size >= targetCount) {
      break;
    }

    window.scrollBy(0, scrollStep);
    await new Promise(r => setTimeout(r, 420));
    scanCurrentDOM();

    if (pinMap.size === lastSize) {
      stagnantCount++;
      if (stagnantCount >= 3) {
        window.scrollBy(0, 900);
        await new Promise(r => setTimeout(r, 600));
        scanCurrentDOM();
      }
      if (stagnantCount >= 6) {
        break;
      }
    } else {
      stagnantCount = 0;
      lastSize = pinMap.size;
    }
  }

  return Array.from(pinMap.values());
}

function renderGallery(pins) {
  gallery.innerHTML = '';
  pinCountBadge.textContent = `${pins.length} pins`;

  if (pins.length === 0) {
    gallery.innerHTML = `
      <div class="empty-state">
        <p>No pins detected on this screen.</p>
        <p class="hint">Ensure you are viewing an active Pinterest board or search feed!</p>
      </div>
    `;
    downloadBtn.disabled = true;
    updateSelectionCount();
    return;
  }

  pins.forEach((pin, index) => {
    const card = document.createElement('div');
    card.className = 'pin-card';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = true;
    checkbox.dataset.index = index;
    checkbox.addEventListener('change', updateSelectionCount);

    const img = document.createElement('img');
    img.src = pin.previewUrl;
    img.loading = 'lazy';

    card.appendChild(checkbox);
    card.appendChild(img);
    gallery.appendChild(card);
  });

  downloadBtn.disabled = false;
  selectAllCheckbox.checked = true;
  updateSelectionCount();
}

function updateSelectionCount() {
  const checkboxes = gallery.querySelectorAll('input[type="checkbox"]:checked');
  const total = gallery.querySelectorAll('input[type="checkbox"]').length;
  selectionSummary.textContent = `${checkboxes.length} / ${total} selected`;
  downloadBtn.disabled = checkboxes.length === 0;
  downloadBtn.textContent = `📦 Download (${checkboxes.length} Pins as 1 ZIP)`;
}

async function startDownloadZip() {
  const checkboxes = gallery.querySelectorAll('input[type="checkbox"]:checked');
  const selectedIndices = Array.from(checkboxes).map(cb => parseInt(cb.dataset.index, 10));
  
  if (selectedIndices.length === 0) return;

  const rawSubfolder = subfolderInput.value.trim().replace(/^[\/\\]+|[\/\\]+$/g, '');
  const subfolder = rawSubfolder ? rawSubfolder + '/' : '';

  downloadBtn.disabled = true;
  scanBtn.disabled = true;
  scanDepthSelect.disabled = true;
  progressContainer.classList.remove('hidden');

  const zip = new JSZip();
  let completed = 0;
  const total = selectedIndices.length;

  for (let i = 0; i < total; i++) {
    const pin = detectedPins[selectedIndices[i]];
    progressText.textContent = `Packing ${i + 1}/${total}: ${pin.filename}`;

    try {
      let response = await fetch(pin.originalUrl);
      if (!response.ok) {
        response = await fetch(pin.previewUrl);
      }
      if (response.ok) {
        const blob = await response.blob();
        zip.file(pin.filename, blob);
        completed++;
      }
    } catch (err) {
      try {
        const fallback = await fetch(pin.previewUrl);
        if (fallback.ok) {
          const blob = await fallback.blob();
          zip.file(pin.filename, blob);
          completed++;
        }
      } catch (e2) {}
    }

    const percent = Math.round(((i + 1) / total) * 88);
    progressBar.style.width = `${percent}%`;
    await new Promise(r => setTimeout(r, 40));
  }

  progressText.textContent = 'Compressing into single ZIP...';
  progressBar.style.width = '94%';

  const zipBlob = await zip.generateAsync({ type: 'blob' });
  const blobUrl = URL.createObjectURL(zipBlob);

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const zipFilename = `${subfolder}pinterest_pins_${timestamp}.zip`;

  chrome.downloads.download({
    url: blobUrl,
    filename: zipFilename,
    conflictAction: 'uniquify'
  }, () => {
    progressBar.style.width = '100%';
    progressText.textContent = `✅ Saved ${completed} pins in 1 ZIP file!`;
    downloadBtn.disabled = false;
    scanBtn.disabled = false;
    scanDepthSelect.disabled = false;
  });
}
