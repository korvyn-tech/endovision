/**
 * EndoVision - Client Application Logic
 * Interface Clínica para Aprimoramento de Radiografias Periapicais
 * Criação Oficial Korvyn &bull; Módulo de Vídeo-Ad e Monetização
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
    user: JSON.parse(localStorage.getItem('endovision_user') || 'null'),
    token: localStorage.getItem('endovision_token') || null,
    pendingPlan: null,
    adCountdownTimer: null,
    videoProgressInterval: null,
    pixPollInterval: null,
  };

  // Elementos do DOM
  const fileUploadInput = document.getElementById('fileUploadInput');
  const dropzone = document.getElementById('dropzone');
  const dropzoneCard = document.getElementById('dropzoneCard');
  const btnUploadHeader = document.getElementById('btnUploadHeader');
  const btnSelectFileCenter = document.getElementById('btnSelectFileCenter');
  const btnChangeImage = document.getElementById('btnChangeImage');
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

  // Monetização & Anúncios Korvyn
  const adBannerSlot = document.getElementById('adBannerSlot');
  const adRemoveTrigger = document.getElementById('adRemoveTrigger');
  const btnContactKorvyn = document.getElementById('btnContactKorvyn');
  const btnOpenProModal = document.getElementById('btnOpenProModal');
  const proBadgeLabel = document.getElementById('proBadgeLabel');

  // Modal Vídeo-Ad Intersticial
  const modalInterstitialAd = document.getElementById('modalInterstitialAd');
  const adTimerCount = document.getElementById('adTimerCount');
  const videoElapsedTimer = document.getElementById('videoElapsedTimer');
  const videoProgressBar = document.getElementById('videoProgressBar');
  const korvynVideoPlayer = document.getElementById('korvynVideoPlayer');
  const videoFallbackContent = document.getElementById('videoFallbackContent');
  const btnSkipAd = document.getElementById('btnSkipAd');
  const btnUpgradeFromAd = document.getElementById('btnUpgradeFromAd');
  const btnInstallPwa = document.getElementById('btnInstallPwa');

  // Modal Pro / Licença
  const modalProPricing = document.getElementById('modalProPricing');
  const btnCloseProModal = document.getElementById('btnCloseProModal');
  const btnSelectMonthly = document.getElementById('btnSelectMonthly');
  const btnSelectLifetime = document.getElementById('btnSelectLifetime');
  const inputLicenseKey = document.getElementById('inputLicenseKey');
  const btnActivateLicense = document.getElementById('btnActivateLicense');

  // Elementos de Autenticação
  const btnOpenAuthModal = document.getElementById('btnOpenAuthModal');
  const userProfileBadge = document.getElementById('userProfileBadge');
  const userAvatarText = document.getElementById('userAvatarText');
  const userNameText = document.getElementById('userNameText');
  const userPlanPill = document.getElementById('userPlanPill');
  const btnLogout = document.getElementById('btnLogout');
  const modalAuth = document.getElementById('modalAuth');
  const btnCloseAuthModal = document.getElementById('btnCloseAuthModal');
  const tabLoginBtn = document.getElementById('tabLoginBtn');
  const tabRegisterBtn = document.getElementById('tabRegisterBtn');
  const formLogin = document.getElementById('formLogin');
  const formRegister = document.getElementById('formRegister');
  const loginEmail = document.getElementById('loginEmail');
  const loginPassword = document.getElementById('loginPassword');
  const loginErrorMsg = document.getElementById('loginErrorMsg');
  const registerName = document.getElementById('registerName');
  const registerEmail = document.getElementById('registerEmail');
  const registerPassword = document.getElementById('registerPassword');
  const registerErrorMsg = document.getElementById('registerErrorMsg');

  // Elementos do Checkout Asaas Pix
  const modalPixCheckout = document.getElementById('modalPixCheckout');
  const btnClosePixModal = document.getElementById('btnClosePixModal');
  const pixPlanTitle = document.getElementById('pixPlanTitle');
  const pixAmountPill = document.getElementById('pixAmountPill');
  const pixLoadingState = document.getElementById('pixLoadingState');
  const pixContent = document.getElementById('pixContent');
  const pixQrImage = document.getElementById('pixQrImage');
  const pixCopyInput = document.getElementById('pixCopyInput');
  const btnCopyPix = document.getElementById('btnCopyPix');
  const pixStatusText = document.getElementById('pixStatusText');
  const pixInvoiceExternalLink = document.getElementById('pixInvoiceExternalLink');
  const pixSuccessScreen = document.getElementById('pixSuccessScreen');
  const btnFinishSuccess = document.getElementById('btnFinishSuccess');

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
  // ==========================================
  // 1. PWA e Registro do Service Worker
  // ==========================================
  let deferredPrompt = null;
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch(err => {
        console.warn('SW register fail:', err);
      });
    });
  }

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (btnInstallPwa) {
      btnInstallPwa.classList.remove('hidden');
    }
  });

  if (btnInstallPwa) {
    btnInstallPwa.addEventListener('click', async () => {
      if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome === 'accepted') {
          btnInstallPwa.classList.add('hidden');
          showToast('EndoVision instalado com sucesso na sua tela inicial!');
        }
        deferredPrompt = null;
      } else {
        showToast('Para instalar: no navegador, acesse o menu de opções e selecione "Instalar Aplicativo" ou "Adicionar à Tela de Início".');
      }
    });
  }

  function syncProStatus() {
    if (state.isPro) {
      if (adBannerSlot) adBannerSlot.classList.add('hidden');
      proBadgeLabel.textContent = 'Versão Pro Ativa';
      btnOpenProModal.classList.add('is-active-pro');
      btnOpenProModal.title = 'Plano Pro Ativo: Sem anúncios, sem vídeos e ilimitado';
    } else {
      if (adBannerSlot) adBannerSlot.classList.remove('hidden');
      proBadgeLabel.textContent = 'Obter Versão Pro';
      btnOpenProModal.classList.remove('is-active-pro');
    }
  }

  function syncUserUI() {
    if (state.user && state.token) {
      if (btnOpenAuthModal) btnOpenAuthModal.classList.add('hidden');
      if (userProfileBadge) userProfileBadge.classList.remove('hidden');
      if (userNameText) userNameText.textContent = state.user.name ? state.user.name.split(' ')[0] : 'Doutor(a)';
      if (userAvatarText) {
        const initials = state.user.name ? state.user.name.split(' ').map(p => p[0]).slice(0, 2).join('') : 'DR';
        userAvatarText.textContent = initials.toUpperCase();
      }

      const isUserPro = state.user.is_pro || state.user.plan === 'pro_monthly' || state.user.plan === 'pro_lifetime';
      if (isUserPro) {
        state.isPro = true;
        localStorage.setItem('endovision_is_pro', 'true');
        if (userPlanPill) {
          userPlanPill.textContent = state.user.plan === 'pro_lifetime' ? '★ Pro Vitalício' : '★ Pro Mensal';
          userPlanPill.classList.add('pro');
        }
      } else {
        if (userPlanPill) {
          userPlanPill.textContent = 'Plano Grátis';
          userPlanPill.classList.remove('pro');
        }
      }
    } else {
      if (btnOpenAuthModal) btnOpenAuthModal.classList.remove('hidden');
      if (userProfileBadge) userProfileBadge.classList.add('hidden');
    }
    syncProStatus();
  }

  // Verifica validade do token na inicialização
  async function fetchUserProfile() {
    if (!state.token) {
      syncUserUI();
      return;
    }
    try {
      const res = await fetch('/api/v1/auth/me', {
        headers: { 'Authorization': `Bearer ${state.token}` }
      });
      if (res.ok) {
        const userData = await res.json();
        state.user = userData;
        localStorage.setItem('endovision_user', JSON.stringify(userData));
        syncUserUI();
      } else {
        logoutUser(false);
      }
    } catch (e) {
      syncUserUI();
    }
  }

  fetchUserProfile();

  // CTA do Patrocinador Korvyn
  if (btnContactKorvyn) {
    btnContactKorvyn.addEventListener('click', () => {
      showToast('Redirecionando para atendimento da Korvyn...');
      window.open('https://api.whatsapp.com/send?text=Olá%20Korvyn!%20Conheci%20o%20EndoVision%20e%20quero%20automatizar%20o%20atendimento%20da%20minha%20clínica.', '_blank');
    });
  }

  // ==========================================
  // 2. Upload / Drag & Drop & Seleção Intuitiva
  // ==========================================
  function openFilePicker() {
    fileUploadInput.value = '';
    fileUploadInput.click();
  }

  // Cliques claros nos botões de envio
  if (btnUploadHeader) btnUploadHeader.addEventListener('click', openFilePicker);
  if (btnSelectFileCenter) btnSelectFileCenter.addEventListener('click', (e) => {
    e.stopPropagation();
    openFilePicker();
  });
  if (btnChangeImage) btnChangeImage.addEventListener('click', openFilePicker);

  // Clicar em qualquer lugar do card de upload (exceto no botão de exemplo)
  if (dropzoneCard) {
    dropzoneCard.addEventListener('click', (e) => {
      if (e.target.closest('#btnSampleQuick')) return;
      openFilePicker();
    });
  }

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
  // 3. Trava de Vídeo-Ad Korvyn (a partir do 2º uso)
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

      // Se for PRO ou 1º uso: processamento imediato!
      if (state.isPro || state.usageCount === 0) {
        if (!state.isPro && state.usageCount === 0) {
          showToast('Primeira análise gratuita! Nos próximos usos, assista ao vídeo da Korvyn ou assine o Pro.');
        }
        state.usageCount++;
        localStorage.setItem('endovision_usage_count', state.usageCount.toString());
        processImage();
      } else {
        triggerKorvynVideoAd();
      }
    };
    reader.readAsDataURL(file);
  }

  function triggerKorvynVideoAd() {
    modalInterstitialAd.classList.remove('hidden');
    let totalSeconds = 5;
    let elapsedSeconds = 0;

    btnSkipAd.disabled = true;
    btnSkipAd.textContent = `Aguarde a reprodução do vídeo (${totalSeconds}s)...`;
    adTimerCount.textContent = `Assista ${totalSeconds}s para continuar`;
    videoElapsedTimer.textContent = `0:00 / 0:05`;
    videoProgressBar.style.width = '0%';

    // Verificar se existe arquivo de vídeo MP4 na pasta de assets
    if (korvynVideoPlayer) {
      korvynVideoPlayer.src = '/assets/videos/korvyn_ad.mp4';
      korvynVideoPlayer.oncanplay = () => {
        korvynVideoPlayer.classList.remove('hidden');
        if (videoFallbackContent) videoFallbackContent.classList.add('hidden');
        korvynVideoPlayer.play().catch(() => {});
      };
      korvynVideoPlayer.onerror = () => {
        // Se ainda não colocou o vídeo físico, mantém a demonstração animada
        korvynVideoPlayer.classList.add('hidden');
        if (videoFallbackContent) videoFallbackContent.classList.remove('hidden');
      };
    }

    clearInterval(state.adCountdownTimer);
    clearInterval(state.videoProgressInterval);

    const startTime = Date.now();
    state.videoProgressInterval = setInterval(() => {
      const elapsedMs = Date.now() - startTime;
      const progress = Math.min(100, (elapsedMs / (totalSeconds * 1000)) * 100);
      videoProgressBar.style.width = `${progress}%`;
      if (progress >= 100) {
        clearInterval(state.videoProgressInterval);
      }
    }, 100);

    state.adCountdownTimer = setInterval(() => {
      elapsedSeconds++;
      const remaining = totalSeconds - elapsedSeconds;
      videoElapsedTimer.textContent = `0:0${Math.min(5, elapsedSeconds)} / 0:05`;

      if (remaining > 0) {
        btnSkipAd.textContent = `Aguarde o vídeo (${remaining}s)...`;
        adTimerCount.textContent = `Assista ${remaining}s para continuar`;
      } else {
        clearInterval(state.adCountdownTimer);
        adTimerCount.textContent = 'Vídeo concluído!';
        btnSkipAd.disabled = false;
        btnSkipAd.textContent = 'Continuar para Radiografia (Grátis)';
      }
    }, 1000);
  }

  btnSkipAd.addEventListener('click', () => {
    modalInterstitialAd.classList.add('hidden');
    clearInterval(state.adCountdownTimer);
    clearInterval(state.videoProgressInterval);
    state.usageCount++;
    localStorage.setItem('endovision_usage_count', state.usageCount.toString());
    processImage();
  });

  btnUpgradeFromAd.addEventListener('click', () => {
    modalInterstitialAd.classList.add('hidden');
    clearInterval(state.adCountdownTimer);
    clearInterval(state.videoProgressInterval);
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
    showToast(`Plano ${planType} ativado com sucesso! Todos os anúncios e vídeos foram removidos.`);

    if (state.currentFile) {
      processImage();
    }
  }

  // Ações de Assinatura via Asaas
  btnSelectMonthly.addEventListener('click', () => {
    initiateAsaasCheckout('monthly');
  });

  btnSelectLifetime.addEventListener('click', () => {
    initiateAsaasCheckout('lifetime');
  });

  // Ativação por Chave (Demo: KORVYNPRO ou KORVYN)
  btnActivateLicense.addEventListener('click', () => {
    const key = (inputLicenseKey.value || '').trim().toUpperCase();
    if (key === 'KORVYNPRO' || key === 'KORVYN' || key === 'CORVINPRO') {
      activateProPlan('Pro Corporativo Korvyn');
    } else {
      showToast('Chave inválida. Utilize a chave oficial: KORVYNPRO', true);
    }
  });

  // ==========================================
  // 4.1 Autenticação e Gestão de Usuário
  // ==========================================
  if (btnOpenAuthModal) {
    btnOpenAuthModal.addEventListener('click', () => {
      modalAuth.classList.remove('hidden');
    });
  }

  if (btnCloseAuthModal) {
    btnCloseAuthModal.addEventListener('click', () => {
      modalAuth.classList.add('hidden');
    });
  }

  if (tabLoginBtn && tabRegisterBtn) {
    tabLoginBtn.addEventListener('click', () => {
      tabLoginBtn.classList.add('active');
      tabRegisterBtn.classList.remove('active');
      formLogin.classList.remove('hidden');
      formRegister.classList.add('hidden');
      if (loginErrorMsg) loginErrorMsg.classList.add('hidden');
    });

    tabRegisterBtn.addEventListener('click', () => {
      tabRegisterBtn.classList.add('active');
      tabLoginBtn.classList.remove('active');
      formRegister.classList.remove('hidden');
      formLogin.classList.add('hidden');
      if (registerErrorMsg) registerErrorMsg.classList.add('hidden');
    });
  }

  if (formLogin) {
    formLogin.addEventListener('submit', async (e) => {
      e.preventDefault();
      loginErrorMsg.classList.add('hidden');
      const submitBtn = document.getElementById('btnSubmitLogin');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Autenticando...';

      try {
        const res = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: loginEmail.value.trim(),
            password: loginPassword.value
          })
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Falha ao autenticar.');
        }

        state.token = data.token;
        state.user = data.user;
        localStorage.setItem('endovision_token', data.token);
        localStorage.setItem('endovision_user', JSON.stringify(data.user));

        modalAuth.classList.add('hidden');
        showToast(`Bem-vindo(a), ${data.user.name}!`);
        syncUserUI();

        if (state.pendingPlan) {
          const plan = state.pendingPlan;
          state.pendingPlan = null;
          initiateAsaasCheckout(plan);
        }
      } catch (err) {
        loginErrorMsg.textContent = err.message;
        loginErrorMsg.classList.remove('hidden');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Entrar no EndoVision';
      }
    });
  }

  if (formRegister) {
    formRegister.addEventListener('submit', async (e) => {
      e.preventDefault();
      registerErrorMsg.classList.add('hidden');
      const submitBtn = document.getElementById('btnSubmitRegister');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Criando conta...';

      try {
        const res = await fetch('/api/v1/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: registerName.value.trim(),
            email: registerEmail.value.trim(),
            password: registerPassword.value
          })
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Falha ao criar conta.');
        }

        state.token = data.token;
        state.user = data.user;
        localStorage.setItem('endovision_token', data.token);
        localStorage.setItem('endovision_user', JSON.stringify(data.user));

        modalAuth.classList.add('hidden');
        showToast(`Conta criada com sucesso! Olá, ${data.user.name}.`);
        syncUserUI();

        if (state.pendingPlan) {
          const plan = state.pendingPlan;
          state.pendingPlan = null;
          initiateAsaasCheckout(plan);
        }
      } catch (err) {
        registerErrorMsg.textContent = err.message;
        registerErrorMsg.classList.remove('hidden');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Criar Minha Conta';
      }
    });
  }

  function logoutUser(showNotification = true) {
    state.token = null;
    state.user = null;
    state.isPro = false;
    localStorage.removeItem('endovision_token');
    localStorage.removeItem('endovision_user');
    localStorage.removeItem('endovision_is_pro');
    syncUserUI();
    if (showNotification) showToast('Você saiu da sua conta.');
  }

  if (btnLogout) {
    btnLogout.addEventListener('click', () => logoutUser(true));
  }

  // ==========================================
  // 4.2 Checkout Asaas Pix em Tempo Real
  // ==========================================
  async function initiateAsaasCheckout(planType) {
    if (!state.token) {
      state.pendingPlan = planType;
      modalProPricing.classList.add('hidden');
      modalAuth.classList.remove('hidden');
      showToast('Por favor, faça login ou crie sua conta para vincular seu Plano Pro.');
      return;
    }

    modalProPricing.classList.add('hidden');
    modalPixCheckout.classList.remove('hidden');

    pixLoadingState.classList.remove('hidden');
    pixContent.classList.add('hidden');
    pixSuccessScreen.classList.add('hidden');

    pixPlanTitle.textContent = planType === 'lifetime' 
      ? 'EndoVision Pro • Acesso Vitalício' 
      : 'EndoVision Pro • Assinatura Mensal';
    pixAmountPill.textContent = planType === 'lifetime' ? 'R$ 149,00' : 'R$ 29,90/mês';

    clearInterval(state.pixPollInterval);

    try {
      const res = await fetch('/api/v1/billing/create-order', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${state.token}`
        },
        body: JSON.stringify({ plan_type: planType })
      });

      const order = await res.json();
      if (!res.ok) {
        throw new Error(order.detail || 'Não foi possível gerar a cobrança no Asaas.');
      }

      pixLoadingState.classList.add('hidden');
      pixContent.classList.remove('hidden');

      // Exibe QR Code Pix (aceita tanto data: quanto raw base64)
      const qrData = order.pix_qr_code || '';
      pixQrImage.src = qrData.startsWith('data:') ? qrData : ('data:image/png;base64,' + qrData);
      pixCopyInput.value = order.pix_copy_paste || '';

      if (order.invoice_url) {
        pixInvoiceExternalLink.href = order.invoice_url;
        pixInvoiceExternalLink.classList.remove('hidden');
      } else {
        pixInvoiceExternalLink.classList.add('hidden');
      }

      // Inicia verificação automática a cada 3 segundos
      startPixPolling(order.payment_id, planType);
    } catch (err) {
      modalPixCheckout.classList.add('hidden');
      showToast(`Erro ao gerar Pix: ${err.message}`, true);
    }
  }

  function startPixPolling(paymentId, planType) {
    clearInterval(state.pixPollInterval);
    state.pixPollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/v1/billing/status/${paymentId}`);
        if (!res.ok) return;
        const data = await res.json();

        if (data.is_paid) {
          clearInterval(state.pixPollInterval);
          state.isPro = true;
          localStorage.setItem('endovision_is_pro', 'true');
          if (state.user) {
            state.user.is_pro = true;
            state.user.plan = data.user_plan;
            localStorage.setItem('endovision_user', JSON.stringify(state.user));
          }
          syncUserUI();

          pixContent.classList.add('hidden');
          pixSuccessScreen.classList.remove('hidden');
        }
      } catch (err) {
        console.warn('Polling error:', err);
      }
    }, 3000);
  }

  if (btnClosePixModal) {
    btnClosePixModal.addEventListener('click', () => {
      modalPixCheckout.classList.add('hidden');
      clearInterval(state.pixPollInterval);
    });
  }

  if (btnFinishSuccess) {
    btnFinishSuccess.addEventListener('click', () => {
      modalPixCheckout.classList.add('hidden');
      clearInterval(state.pixPollInterval);
      if (state.currentFile) {
        processImage();
      }
    });
  }

  if (btnCopyPix) {
    btnCopyPix.addEventListener('click', async () => {
      if (!pixCopyInput.value) return;
      try {
        await navigator.clipboard.writeText(pixCopyInput.value);
        showToast('Código Pix Copia e Cola copiado com sucesso!');
      } catch (err) {
        pixCopyInput.select();
        document.execCommand('copy');
        showToast('Código Pix copiado!');
      }
    });
  }

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
    a.download = `endovision_korvyn_${state.currentPreset}_${Date.now()}.png`;
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
