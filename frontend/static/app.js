/**
 * EndoVision - Client Application Logic
 * Interface Clínica para Aprimoramento de Radiografias Periapicais
 * Módulo de Monetização: Freemium, Ads & EndoVision Pro
 */

document.addEventListener('DOMContentLoaded', () => {
  // Estado da Aplicação e Monetização
  const state = {
    currentFile: null,
    currentPreset: 'apical_enhancement',
    originalImageSrc: null,
    enhancedImageSrc: null,
    splitPosition: 50,
    zoomLevel: 1.0,
    isDraggingSplit: false,
    debounceTimer: null,
    usageCount: parseInt(localStorage.getItem('endovision_usage_count') || '0', 10),
    isPro: localStorage.getItem('endovision_is_pro') === 'true',
    adCountdownTimer: null,
  };

  // Elementos do DOM
  const fileUploadInput = document.getElementById('fileUploadInput');
  const dropzone = document.getElementById('dropzone');
  const comparisonStage = document.getElementById('comparisonStage');
  const imageWrapper = document.getElementById('imageWrapper');
  const imgOriginal = document.getElementById('imgOriginal');
  const imgEnhanced = document.getElementById('imgEnhanced');
  const overlayContainer = document.getElementById('overlayContainer');
  const splitDivider = document.getElementById('splitDivider');
  const badgeEnhancedPreset = document.getElementById('badgeEnhancedPreset');

  // Botoes e Acoes
  const presetsBar = document.getElementById('presetsBar');
  const btnSampleOverexposed = document.getElementById('btnSampleOverexposed');
  const btnSampleQuick = document.getElementById('btnSampleQuick');
  const btnDownload = document.getElementById('btnDownload');
  const btnCopyClipboard = document.getElementById('btnCopyClipboard');
  const btnResetAdjustments = document.getElementById('btnResetAdjustments');

  // Monetização & Ads
  const adBannerSlot = document.getElementById('adBannerSlot');
  const adRemoveTrigger = document.getElementById('adRemoveTrigger');
  const btnOpenProModal = document.getElementById('btnOpenProModal');
  const proBadgeLabel = document.getElementById('proBadgeLabel');
  const modalInterstitialAd = document.getElementById('modalInterstitialAd');
  const adTimerCount = document.getElementById('adTimerCount');
  const btnSkipAd = document.getElementById('btnSkipAd');
  const btnUpgradeFromAd = document.getElementById('btnUpgradeFromAd');
  const modalProPricing = document.getElementById('modalProPricing');
  const btnCloseProModal = document.getElementById('btnCloseProModal');
  const btnSelectMonthly = document.getElementById('btnSelectMonthly');
  const btnSelectLifetime = document.getElementById('btnSelectLifetime');
  const inputLicenseKey = document.getElementById('inputLicenseKey');
  const btnActivateLicense = document.getElementById('btnActivateLicense');

  // Zoom
  const btnZoomIn = document.getElementById('btnZoomIn');
  const btnZoomOut = document.getElementById('btnZoomOut');
  const btnZoomReset = document.getElementById('btnZoomReset');
  const zoomLevelText = document.getElementById('zoomLevelText');

  // Sliders e Controles Manuais
  const sliderGamma = document.getElementById('sliderGamma');
  const sliderClahe = document.getElementById('sliderClahe');
  const sliderUnsharp = document.getElementById('sliderUnsharp');
  const checkInvert = document.getElementById('checkInvert');
  const checkNormalize = document.getElementById('checkNormalize');
  const valGamma = document.getElementById('valGamma');
  const valClahe = document.getElementById('valClahe');
  const valUnsharp = document.getElementById('valUnsharp');

  // Painel de Metricas
  const processingTimeBadge = document.getElementById('processingTimeBadge');
  const contrastGainValue = document.getElementById('contrastGainValue');
  const michelsonOrig = document.getElementById('michelsonOrig');
  const michelsonEnh = document.getElementById('michelsonEnh');
  const brightnessOrig = document.getElementById('brightnessOrig');
  const brightnessEnh = document.getElementById('brightnessEnh');
  const toast = document.getElementById('toastNotification');

  // ==========================================
  // 1. Inicializacao do Estado Pro / Ads
  // ==========================================
  function syncProStatus() {
    if (state.isPro) {
      if (adBannerSlot) adBannerSlot.classList.add('hidden');
      proBadgeLabel.textContent = 'Versão Pro Ativa';
      btnOpenProModal.classList.add('is-active-pro');
      btnOpenProModal.title = 'Plano Pro Ativo: Sem anúncios e ilimitado';
    } else {
      if (adBannerSlot) adBannerSlot.classList.remove('hidden');
      proBadgeLabel.textContent = 'Obter Versão Pro';
      btnOpenProModal.classList.remove('is-active-pro');
    }
  }

  syncProStatus();

  // ==========================================
  // 2. Upload / Drag & Drop
  // ==========================================
  if (dropzone) {
    ['dragenter', 'dragover'].forEach(evt => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(evt => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        handleImageSelection(files[0]);
      }
    });
  }

  if (fileUploadInput) {
    fileUploadInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleImageSelection(e.target.files[0]);
      }
    });
  }

  [btnSampleOverexposed, btnSampleQuick].forEach(btn => {
    if (btn) {
      btn.addEventListener('click', () => {
        loadSyntheticDentalXray();
      });
    }
  });

  // Radiografia Sintetica
  function loadSyntheticDentalXray() {
    showToast('Gerando simulação de radiografia periapical...');
    const canvas = document.createElement('canvas');
    canvas.width = 600;
    canvas.height = 700;
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = '#b8bec7';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imgData.data;
    for (let i = 0; i < data.length; i += 4) {
      const noise = (Math.random() - 0.5) * 25;
      data[i] = Math.min(255, Math.max(0, data[i] + noise));
      data[i+1] = data[i];
      data[i+2] = data[i];
    }
    ctx.putImageData(imgData, 0, 0);

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(220, 140);
    ctx.bezierCurveTo(200, 240, 240, 320, 250, 420);
    ctx.bezierCurveTo(260, 520, 280, 620, 295, 650);
    ctx.bezierCurveTo(310, 620, 330, 520, 340, 420);
    ctx.bezierCurveTo(350, 320, 390, 240, 370, 140);
    ctx.closePath();
    ctx.fillStyle = 'rgba(235, 240, 245, 0.45)';
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(290, 240);
    ctx.bezierCurveTo(292, 340, 294, 460, 297, 642);
    ctx.lineWidth = 3.5;
    ctx.strokeStyle = 'rgba(120, 125, 135, 0.35)';
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(297, 658, 22, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(140, 145, 155, 0.25)';
    ctx.fill();
    ctx.restore();

    canvas.toBlob((blob) => {
      const file = new File([blob], 'rx_periapical_lavada.png', { type: 'image/png' });
      handleImageSelection(file);
    }, 'image/png');
  }

  // ==========================================
  // 3. Trava de Monetização (Intersticial pós-1º uso)
  // ==========================================
  function handleImageSelection(file) {
    if (!file.type.startsWith('image/')) {
      showToast('Por favor, selecione um arquivo de imagem válido (PNG, JPEG, TIFF).', true);
      return;
    }

    state.currentFile = file;

    const reader = new FileReader();
    reader.onload = (e) => {
      state.originalImageSrc = e.target.result;
      imgOriginal.src = e.target.result;

      dropzone.classList.add('hidden');
      comparisonStage.classList.remove('hidden');

      // Checagem de Monetização:
      // Se for PRO: executa direto sem interrupções!
      // Se for Grátis no 1º uso: executa cortesia e avisa!
      // Se for Grátis a partir do 2º uso: exige assistir ao anúncio antes de processar!
      if (state.isPro || state.usageCount === 0) {
        if (!state.isPro && state.usageCount === 0) {
          showToast('Primeira análise gratuita! A partir da próxima, assista a um anúncio ou assine o Pro.');
        }
        state.usageCount++;
        localStorage.setItem('endovision_usage_count', state.usageCount.toString());
        processImage();
      } else {
        triggerInterstitialAd();
      }
    };
    reader.readAsDataURL(file);
  }

  function triggerInterstitialAd() {
    modalInterstitialAd.classList.remove('hidden');
    let secondsLeft = 5;
    btnSkipAd.disabled = true;
    btnSkipAd.textContent = `Aguarde ${secondsLeft}s...`;
    adTimerCount.textContent = `Aguarde ${secondsLeft}s para continuar`;

    clearInterval(state.adCountdownTimer);
    state.adCountdownTimer = setInterval(() => {
      secondsLeft--;
      if (secondsLeft > 0) {
        btnSkipAd.textContent = `Aguarde ${secondsLeft}s...`;
        adTimerCount.textContent = `Aguarde ${secondsLeft}s para continuar`;
      } else {
        clearInterval(state.adCountdownTimer);
        adTimerCount.textContent = 'Anúncio concluído';
        btnSkipAd.disabled = false;
        btnSkipAd.textContent = 'Continuar com Imagem (Grátis)';
      }
    }, 1000);
  }

  btnSkipAd.addEventListener('click', () => {
    modalInterstitialAd.classList.add('hidden');
    state.usageCount++;
    localStorage.setItem('endovision_usage_count', state.usageCount.toString());
    processImage();
  });

  btnUpgradeFromAd.addEventListener('click', () => {
    modalInterstitialAd.classList.add('hidden');
    clearInterval(state.adCountdownTimer);
    modalProPricing.classList.remove('hidden');
  });

  // ==========================================
  // 4. Modal de Preços & Assinatura Pro
  // ==========================================
  [btnOpenProModal, adRemoveTrigger].forEach(btn => {
    if (btn) {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        modalProPricing.classList.remove('hidden');
      });
    }
  });

  btnCloseProModal.addEventListener('click', () => {
    modalProPricing.classList.add('hidden');
  });

  function activateProPlan(planType) {
    state.isPro = true;
    localStorage.setItem('endovision_is_pro', 'true');
    syncProStatus();
    modalProPricing.classList.add('hidden');
    showToast(`Parabéns! Plano ${planType} ativado com sucesso. Todos os anúncios foram removidos.`);

    // Se já havia uma imagem na fila, processa imediatamente
    if (state.currentFile) {
      processImage();
    }
  }

  btnSelectMonthly.addEventListener('click', () => {
    activateProPlan('Mensal (R$ 29,90/mês)');
  });

  btnSelectLifetime.addEventListener('click', () => {
    activateProPlan('Vitalício (R$ 149)');
  });

  // Ativação por Chave de Licença (Demo: CORVINPRO)
  btnActivateLicense.addEventListener('click', () => {
    const key = (inputLicenseKey.value || '').trim().toUpperCase();
    if (key === 'CORVINPRO' || key === 'ENDOVISION') {
      activateProPlan('Pro via Chave Corporativa');
    } else {
      showToast('Chave inválida. Utilize a chave de demonstração: CORVINPRO', true);
    }
  });

  // ==========================================
  // 5. Processamento via API REST
  // ==========================================
  async function processImage() {
    if (!state.currentFile) return;

    processingTimeBadge.textContent = 'Processando...';

    const formData = new FormData();
    formData.append('file', state.currentFile);
    formData.append('preset', state.currentPreset);

    if (state.currentPreset === 'custom') {
      formData.append('gamma', sliderGamma.value);
      formData.append('clahe_clip', sliderClahe.value);
      formData.append('unsharp_strength', sliderUnsharp.value);
      formData.append('invert', checkInvert.checked);
      formData.append('normalize_range', checkNormalize.checked);
    }

    try {
      const response = await fetch('/api/v1/enhance', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Erro ao processar radiografia');
      }

      const result = await response.json();
      renderResults(result);
    } catch (err) {
      console.error(err);
      showToast(`Falha no processamento: ${err.message}`, true);
      processingTimeBadge.textContent = 'Erro';
    }
  }

  function renderResults(result) {
    state.enhancedImageSrc = result.image_base64;
    imgEnhanced.src = result.image_base64;

    const presetNames = {
      apical_enhancement: 'Ápice & Forame',
      calcified_canals: 'Canais Calcificados',
      contrast_recovery: 'Recuperar Exposição',
      negative_invert: 'Inversão Negativo',
      custom: 'Ajuste Manual',
    };
    badgeEnhancedPreset.textContent = presetNames[result.preset_applied] || 'Aprimorado';

    processingTimeBadge.textContent = `${result.processing_time_ms} ms`;

    const origRms = result.original_metrics.rms_contrast;
    const enhRms = result.enhanced_metrics.rms_contrast;
    const gainPct = origRms > 0 ? Math.round(((enhRms - origRms) / origRms) * 100) : 0;
    contrastGainValue.textContent = gainPct >= 0 ? `+${gainPct}%` : `${gainPct}%`;

    michelsonOrig.textContent = result.original_metrics.michelson_contrast.toFixed(2);
    michelsonEnh.textContent = result.enhanced_metrics.michelson_contrast.toFixed(2);

    brightnessOrig.textContent = Math.round(result.original_metrics.mean_brightness);
    brightnessEnh.textContent = Math.round(result.enhanced_metrics.mean_brightness);

    btnDownload.disabled = false;
    btnCopyClipboard.disabled = false;

    updateSplitSlider(state.splitPosition);
  }

  // ==========================================
  // 6. Split Slider Interativo
  // ==========================================
  function updateSplitSlider(percentage) {
    state.splitPosition = Math.max(0, Math.min(100, percentage));
    overlayContainer.style.clipPath = `polygon(${state.splitPosition}% 0, 100% 0, 100% 100%, ${state.splitPosition}% 100%)`;
    splitDivider.style.left = `${state.splitPosition}%`;
  }

  function handleSplitMove(clientX) {
    const rect = imageWrapper.getBoundingClientRect();
    if (rect.width === 0) return;
    const offsetX = clientX - rect.left;
    const pct = (offsetX / rect.width) * 100;
    updateSplitSlider(pct);
  }

  imageWrapper.addEventListener('mousedown', (e) => {
    state.isDraggingSplit = true;
    handleSplitMove(e.clientX);
  });

  window.addEventListener('mousemove', (e) => {
    if (state.isDraggingSplit) {
      handleSplitMove(e.clientX);
    }
  });

  window.addEventListener('mouseup', () => {
    state.isDraggingSplit = false;
  });

  imageWrapper.addEventListener('touchstart', (e) => {
    if (e.touches && e.touches.length === 1) {
      state.isDraggingSplit = true;
      handleSplitMove(e.touches[0].clientX);
    }
  });

  window.addEventListener('touchmove', (e) => {
    if (state.isDraggingSplit && e.touches && e.touches.length === 1) {
      handleSplitMove(e.touches[0].clientX);
    }
  });

  window.addEventListener('touchend', () => {
    state.isDraggingSplit = false;
  });

  // ==========================================
  // 7. Presets & Controles
  // ==========================================
  presetsBar.addEventListener('click', (e) => {
    const btn = e.target.closest('.segmented-btn');
    if (!btn) return;

    document.querySelectorAll('.segmented-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    state.currentPreset = btn.dataset.preset;
    processImage();
  });

  function bindSlider(slider, labelElem, format = (v) => v) {
    slider.addEventListener('input', () => {
      labelElem.textContent = format(slider.value);
      activateCustomMode();
    });
  }

  bindSlider(sliderGamma, valGamma, (v) => parseFloat(v).toFixed(2));
  bindSlider(sliderClahe, valClahe, (v) => parseFloat(v).toFixed(1));
  bindSlider(sliderUnsharp, valUnsharp, (v) => parseFloat(v).toFixed(1));

  [checkInvert, checkNormalize].forEach(toggle => {
    toggle.addEventListener('change', () => {
      activateCustomMode();
    });
  });

  function activateCustomMode() {
    state.currentPreset = 'custom';
    document.querySelectorAll('.segmented-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.preset === 'custom');
    });

    clearTimeout(state.debounceTimer);
    state.debounceTimer = setTimeout(() => {
      processImage();
    }, 200);
  }

  btnResetAdjustments.addEventListener('click', () => {
    sliderGamma.value = '1.2';
    valGamma.textContent = '1.20';
    sliderClahe.value = '3.5';
    valClahe.textContent = '3.5';
    sliderUnsharp.value = '1.4';
    valUnsharp.textContent = '1.4';
    checkInvert.checked = false;
    checkNormalize.checked = true;

    const defaultBtn = document.querySelector('[data-preset="apical_enhancement"]');
    if (defaultBtn) defaultBtn.click();
  });

  // ==========================================
  // 8. Zoom
  // ==========================================
  function setZoom(level) {
    state.zoomLevel = Math.max(0.5, Math.min(3.0, level));
    imageWrapper.style.transform = `scale(${state.zoomLevel})`;
    zoomLevelText.textContent = `${Math.round(state.zoomLevel * 100)}%`;
  }

  btnZoomIn.addEventListener('click', () => setZoom(state.zoomLevel + 0.25));
  btnZoomOut.addEventListener('click', () => setZoom(state.zoomLevel - 0.25));
  btnZoomReset.addEventListener('click', () => setZoom(1.0));

  // ==========================================
  // 9. Exportacao
  // ==========================================
  btnDownload.addEventListener('click', () => {
    if (!state.enhancedImageSrc) return;
    const a = document.createElement('a');
    a.href = state.enhancedImageSrc;
    a.download = `endovision_${state.currentPreset}_${Date.now()}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    showToast('Radiografia aprimorada exportada em alta resolução.');
  });

  btnCopyClipboard.addEventListener('click', async () => {
    if (!state.enhancedImageSrc) return;
    try {
      const res = await fetch(state.enhancedImageSrc);
      const blob = await res.blob();
      await navigator.clipboard.write([
        new ClipboardItem({ 'image/png': blob })
      ]);
      showToast('Imagem copiada para a área de transferência.');
    } catch (err) {
      console.warn('Falha no ClipboardItem:', err);
      showToast('Navegador bloqueou a cópia direta. Utilize o botão Exportar.', true);
    }
  });

  function showToast(message, isError = false) {
    toast.textContent = message;
    toast.style.borderColor = isError ? 'rgba(239, 68, 68, 0.4)' : 'rgba(56, 189, 248, 0.4)';
    toast.style.color = isError ? '#f87171' : 'var(--text-primary)';
    toast.classList.remove('hidden');

    setTimeout(() => {
      toast.classList.add('hidden');
    }, 3500);
  }
});
