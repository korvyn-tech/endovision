/**
 * EndoVision - Client Application Logic
 * Interface Clínica para Aprimoramento de Radiografias Periapicais
 */

document.addEventListener('DOMContentLoaded', () => {
  // Estado da Aplicação
  const state = {
    currentFile: null,
    currentPreset: 'apical_enhancement',
    originalImageSrc: null,
    enhancedImageSrc: null,
    splitPosition: 50, // porcentagem (0 a 100)
    zoomLevel: 1.0,
    isDraggingSplit: false,
    debounceTimer: null,
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
  // 1. Inicializacao e Eventos de Upload / Drag & Drop
  // ==========================================

  // Drag & drop na dropzone
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
    if (files.length > 0) {
      handleImageSelection(files[0]);
    }
  });

  fileUploadInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleImageSelection(e.target.files[0]);
    }
  });

  // Botoes de Exemplo Sintetico Clínico
  [btnSampleOverexposed, btnSampleQuick].forEach(btn => {
    if (btn) {
      btn.addEventListener('click', () => {
        loadSyntheticDentalXray();
      });
    }
  });

  // ==========================================
  // 2. Gerador de Radiografia Periapical Sintetica
  // ==========================================
  function loadSyntheticDentalXray() {
    showToast('Gerando simulação de radiografia periapical com superexposição...');
    const canvas = document.createElement('canvas');
    canvas.width = 600;
    canvas.height = 700;
    const ctx = canvas.getContext('2d');

    // Fundo cinza lavado (radiografia superexposta no negatoscopio)
    ctx.fillStyle = '#b8bec7';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Ruido granulado característico de pelicula de raio-X
    const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imgData.data;
    for (let i = 0; i < data.length; i += 4) {
      const noise = (Math.random() - 0.5) * 25;
      data[i] = Math.min(255, Math.max(0, data[i] + noise));
      data[i+1] = data[i];
      data[i+2] = data[i];
    }
    ctx.putImageData(imgData, 0, 0);

    // Desenhar contorno radiopaco da coroa e raiz dentaria
    ctx.save();
    ctx.beginPath();
    // Coroa dentaria
    ctx.moveTo(220, 140);
    ctx.bezierCurveTo(200, 240, 240, 320, 250, 420);
    // Raiz afilando em direcao ao ápice
    ctx.bezierCurveTo(260, 520, 280, 620, 295, 650); // Forame apical
    ctx.bezierCurveTo(310, 620, 330, 520, 340, 420);
    ctx.bezierCurveTo(350, 320, 390, 240, 370, 140);
    ctx.closePath();
    ctx.fillStyle = 'rgba(235, 240, 245, 0.45)'; // Esmalte/Dentina radiopacos lavados
    ctx.fill();

    // Canal radicular endodontico (radiolúcido - escuro)
    ctx.beginPath();
    ctx.moveTo(290, 240); // Camara pulpar
    ctx.bezierCurveTo(292, 340, 294, 460, 297, 642); // Constricao apical
    ctx.lineWidth = 3.5;
    ctx.strokeStyle = 'rgba(120, 125, 135, 0.35)'; // Quase invisivel na radiografia lavada!
    ctx.stroke();

    // Ligamento periodontal e trabeculado osseo periapical
    ctx.beginPath();
    ctx.arc(297, 658, 22, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(140, 145, 155, 0.25)'; // Lesao periapical sutil
    ctx.fill();
    ctx.restore();

    canvas.toBlob((blob) => {
      const file = new File([blob], 'rx_periapical_superexposta.png', { type: 'image/png' });
      handleImageSelection(file);
    }, 'image/png');
  }

  // ==========================================
  // 3. Processamento e Chamada da API
  // ==========================================
  function handleImageSelection(file) {
    if (!file.type.startsWith('image/')) {
      showToast('Por favor, selecione um arquivo de imagem válido (PNG, JPEG, TIFF).', true);
      return;
    }

    state.currentFile = file;

    // Leitura local para exibicao imediata do Original
    const reader = new FileReader();
    reader.onload = (e) => {
      state.originalImageSrc = e.target.result;
      imgOriginal.src = e.target.result;

      // Trocar da Dropzone para o Comparador
      dropzone.classList.add('hidden');
      comparisonStage.classList.remove('hidden');

      // Executar aprimoramento
      processImage();
    };
    reader.readAsDataURL(file);
  }

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

    // Atualizar badge do preset
    const presetNames = {
      apical_enhancement: 'Ápice & Forame',
      calcified_canals: 'Canais Calcificados',
      contrast_recovery: 'Recuperar Exposição',
      negative_invert: 'Inversão Negativo',
      custom: 'Ajuste Manual',
    };
    badgeEnhancedPreset.textContent = presetNames[result.preset_applied] || 'Aprimorado';

    // Atualizar Metricas
    processingTimeBadge.textContent = `${result.processing_time_ms} ms`;

    // Calculo do ganho percentual de contraste RMS
    const origRms = result.original_metrics.rms_contrast;
    const enhRms = result.enhanced_metrics.rms_contrast;
    const gainPct = origRms > 0 ? Math.round(((enhRms - origRms) / origRms) * 100) : 0;
    contrastGainValue.textContent = gainPct >= 0 ? `+${gainPct}%` : `${gainPct}%`;

    michelsonOrig.textContent = result.original_metrics.michelson_contrast.toFixed(2);
    michelsonEnh.textContent = result.enhanced_metrics.michelson_contrast.toFixed(2);

    brightnessOrig.textContent = Math.round(result.original_metrics.mean_brightness);
    brightnessEnh.textContent = Math.round(result.enhanced_metrics.mean_brightness);

    // Habilitar botoes de acao
    btnDownload.disabled = false;
    btnCopyClipboard.disabled = false;

    updateSplitSlider(state.splitPosition);
  }

  // ==========================================
  // 4. Split Slider Interativo (Antes / Depois)
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

  // Suporte a Touch para iPad / Tablet odontológico
  imageWrapper.addEventListener('touchstart', (e) => {
    if (e.touches.length === 1) {
      state.isDraggingSplit = true;
      handleSplitMove(e.touches[0].clientX);
    }
  });

  window.addEventListener('touchmove', (e) => {
    if (state.isDraggingSplit && e.touches.length === 1) {
      handleSplitMove(e.touches[0].clientX);
    }
  });

  window.addEventListener('touchend', () => {
    state.isDraggingSplit = false;
  });

  // ==========================================
  // 5. Presets & Controles Manuais
  // ==========================================
  presetsBar.addEventListener('click', (e) => {
    const pill = e.target.closest('.preset-pill');
    if (!pill) return;

    document.querySelectorAll('.preset-pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');

    state.currentPreset = pill.dataset.preset;
    processImage();
  });

  // Atualizacao de labels dos sliders
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
    document.querySelectorAll('.preset-pill').forEach(p => {
      p.classList.toggle('active', p.dataset.preset === 'custom');
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

    // Voltar para preset padrao
    document.querySelector('[data-preset="apical_enhancement"]').click();
  });

  // ==========================================
  // 6. Zoom & Pan
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
  // 7. Acoes de Exportacao
  // ==========================================
  btnDownload.addEventListener('click', () => {
    if (!state.enhancedImageSrc) return;
    const a = document.createElement('a');
    a.href = state.enhancedImageSrc;
    a.download = `endovision_${state.currentPreset}_${Date.now()}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    showToast('Radiografia aprimorada exportada em alta resolução!');
  });

  btnCopyClipboard.addEventListener('click', async () => {
    if (!state.enhancedImageSrc) return;
    try {
      const res = await fetch(state.enhancedImageSrc);
      const blob = await res.blob();
      await navigator.clipboard.write([
        new ClipboardItem({ 'image/png': blob })
      ]);
      showToast('Imagem copiada para a área de transferência! Pronta para colar no prontuário.');
    } catch (err) {
      console.warn('Falha no ClipboardItem:', err);
      showToast('Navegador bloqueou a cópia direta. Use o botão Baixar.', true);
    }
  });

  // Toast Helper
  function showToast(message, isError = false) {
    toast.textContent = message;
    toast.style.borderColor = isError ? '#ef4444' : 'var(--accent-cyan)';
    toast.style.color = isError ? '#f87171' : 'var(--text-main)';
    toast.classList.remove('hidden');

    setTimeout(() => {
      toast.classList.add('hidden');
    }, 3500);
  }
});
