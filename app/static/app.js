const state = {
  language: "en",
  scenarios: null,
  assessment: null,
  paymentType: "traditional",
  dataSource: "live",
  jofsMode: null,
  liveAccounts: [],
  liveBeneficiaries: [],
};

const translations = {
  en: {
    partnerBank: "Partner Bank Demo",
    poweredBy: "Protected by",
    sandboxMode: "JOFS sandbox-ready",
    eyebrow: "Embedded fraud prevention",
    heroTitle: "Protection at the moment of decision.",
    heroText: "TrustTrace adds an explainable AI risk check between payment confirmation and final authorization.",
    sharedEngine: "One shared risk engine",
    twoEcosystems: "Traditional + Web3",
    traditionalTab: "Bank payment",
    traditionalTabSub: "JOFS + payment intelligence",
    web3Tab: "Web3 approval",
    web3TabSub: "Blockchain intelligence",
    bankingJourney: "Existing banking journey",
    confirmTransfer: "Confirm transfer",
    embedded: "Embedded",
    demoScenario: "Demo scenario",
    safeRetailer: "Trusted retailer — safe",
    fakeVisa: "Fake e-visa merchant — suspicious",
    dataSourceLive: "Live JOFS account",
    dataSourceDemo: "Demo scenario (synthetic)",
    liveAccountLabel: "JOFS account",
    liveBeneficiaryLabel: "Beneficiary",
    demoScenarioNotice: "Synthetic model-input scenario for demonstration — not a real JOFS account.",
    fromAccount: "From account",
    available: "Available",
    beneficiary: "Beneficiary",
    merchant: "Merchant",
    amount: "Amount",
    paymentDomain: "Payment domain",
    bankNotice: "The bank remains in control of authorization. TrustTrace provides an explainable advisory risk signal.",
    confirmPayment: "Confirm payment",
    dataContext: "Data context",
    traditionalSignals: "Traditional payment signals",
    accountContext: "Account context",
    accountContextSub: "Account, balance and beneficiary",
    merchantIntel: "Merchant intelligence",
    merchantIntelSub: "Verification and scam history",
    websiteIntel: "Website intelligence",
    websiteIntelSub: "Domain trust and phishing reports",
    behaviour: "Behavioural signals",
    behaviourSub: "Amount, device, location and attempts",
    paymentRequest: "Payment request",
    lowRisk: "Low risk",
    review: "Review",
    highRisk: "High risk",
    walletJourney: "Existing wallet journey",
    approveRequest: "Approve token request",
    walletIntegrated: "Wallet-integrated",
    verifiedContract: "Verified contract — safe",
    maliciousContract: "Malicious approval — suspicious",
    connectedWallet: "Connected wallet",
    connected: "Connected",
    contractAddress: "Smart-contract address",
    token: "Token",
    permission: "Requested permission",
    limited: "Limited approval",
    unlimited: "Unlimited approval",
    web3Notice: "TrustTrace analyzes public blockchain and contract data before the wallet submits the approval.",
    approveTransaction: "Approve transaction",
    web3Signals: "Blockchain/Web3 signals",
    blockchainHistory: "Blockchain history",
    blockchainHistorySub: "Public transaction context",
    walletReputation: "Wallet reputation",
    walletReputationSub: "Known reports and relationships",
    contractRisk: "Smart-contract risk",
    contractRiskSub: "Verification, age and activity",
    tokenPermissions: "Token permissions",
    tokenPermissionsSub: "Limited or unlimited access",
    approvalRequest: "Approval request",
    prototypeFooter: "Hackathon prototype — advisory risk decisions only.",
    analyzing: "Analyzing this payment…",
    analysisSubtitle: "The transaction has not been authorized yet.",
    riskAssessment: "Risk assessment",
    whyFlagged: "Why this decision?",
    dataAnalyzed: "Data analyzed",
    cancelPayment: "Cancel payment",
    continueAction: "Continue",
    checksTraditional: [
      "Retrieving JOFS account context",
      "Checking beneficiary and merchant",
      "Analyzing website reputation",
      "Comparing device and location",
      "Scoring behavioural fraud signals",
      "Generating a plain-language explanation"
    ],
    checksWeb3: [
      "Reading blockchain transaction context",
      "Checking wallet reputation",
      "Inspecting smart-contract verification",
      "Analyzing token permissions",
      "Tracing suspicious wallet relationships",
      "Generating a plain-language explanation"
    ],
    completedSafe: "Payment flow completed in demo mode.",
    completedBlocked: "Payment cancelled before authorization.",
    error: "The prototype could not complete the assessment. Please retry."
  },
  ar: {
    partnerBank: "نموذج البنك الشريك",
    poweredBy: "محمي بواسطة",
    sandboxMode: "جاهز لبيئة JOFS التجريبية",
    eyebrow: "منع الاحتيال المدمج",
    heroTitle: "الحماية في لحظة اتخاذ القرار.",
    heroText: "يضيف TrustTrace فحص مخاطر بالذكاء الاصطناعي بين تأكيد الدفع والموافقة النهائية.",
    sharedEngine: "محرك مخاطر موحد",
    twoEcosystems: "مدفوعات تقليدية + Web3",
    traditionalTab: "دفع بنكي",
    traditionalTabSub: "JOFS + معلومات الدفع",
    web3Tab: "موافقة Web3",
    web3TabSub: "معلومات البلوكشين",
    bankingJourney: "رحلة بنكية قائمة",
    confirmTransfer: "تأكيد التحويل",
    embedded: "مدمج",
    demoScenario: "سيناريو العرض",
    safeRetailer: "تاجر موثوق — آمن",
    fakeVisa: "موقع تأشيرة مزيف — مشبوه",
    dataSourceLive: "حساب JOFS حقيقي",
    dataSourceDemo: "سيناريو تجريبي (بيانات اصطناعية)",
    liveAccountLabel: "حساب JOFS",
    liveBeneficiaryLabel: "المستفيد",
    demoScenarioNotice: "سيناريو اصطناعي لإدخال النموذج لأغراض العرض — وليس حساب JOFS حقيقي.",
    fromAccount: "من الحساب",
    available: "الرصيد المتاح",
    beneficiary: "المستفيد",
    merchant: "التاجر",
    amount: "المبلغ",
    paymentDomain: "نطاق الدفع",
    bankNotice: "يبقى قرار الموافقة بيد البنك. يقدم TrustTrace إشارة مخاطر استشارية قابلة للتفسير.",
    confirmPayment: "تأكيد الدفع",
    dataContext: "سياق البيانات",
    traditionalSignals: "إشارات الدفع التقليدي",
    accountContext: "سياق الحساب",
    accountContextSub: "الحساب والرصيد والمستفيد",
    merchantIntel: "معلومات التاجر",
    merchantIntelSub: "التحقق وسجل الاحتيال",
    websiteIntel: "معلومات الموقع",
    websiteIntelSub: "موثوقية النطاق وبلاغات التصيد",
    behaviour: "الإشارات السلوكية",
    behaviourSub: "المبلغ والجهاز والموقع والمحاولات",
    paymentRequest: "طلب الدفع",
    lowRisk: "مخاطر منخفضة",
    review: "مراجعة",
    highRisk: "مخاطر مرتفعة",
    walletJourney: "رحلة محفظة قائمة",
    approveRequest: "الموافقة على طلب الرمز",
    walletIntegrated: "مدمج في المحفظة",
    verifiedContract: "عقد موثق — آمن",
    maliciousContract: "موافقة ضارة — مشبوهة",
    connectedWallet: "المحفظة المتصلة",
    connected: "متصل",
    contractAddress: "عنوان العقد الذكي",
    token: "الرمز",
    permission: "الصلاحية المطلوبة",
    limited: "صلاحية محدودة",
    unlimited: "صلاحية غير محدودة",
    web3Notice: "يحلل TrustTrace بيانات البلوكشين والعقد العامة قبل أن ترسل المحفظة الموافقة.",
    approveTransaction: "الموافقة على العملية",
    web3Signals: "إشارات البلوكشين وWeb3",
    blockchainHistory: "سجل البلوكشين",
    blockchainHistorySub: "سياق المعاملات العامة",
    walletReputation: "سمعة المحفظة",
    walletReputationSub: "البلاغات والعلاقات المعروفة",
    contractRisk: "مخاطر العقد الذكي",
    contractRiskSub: "التوثيق والعمر والنشاط",
    tokenPermissions: "صلاحيات الرموز",
    tokenPermissionsSub: "وصول محدود أو غير محدود",
    approvalRequest: "طلب الموافقة",
    prototypeFooter: "نموذج هاكاثون — قرارات مخاطر استشارية فقط.",
    analyzing: "جارٍ تحليل عملية الدفع…",
    analysisSubtitle: "لم تتم الموافقة على العملية بعد.",
    riskAssessment: "تقييم المخاطر",
    whyFlagged: "لماذا صدر هذا القرار؟",
    dataAnalyzed: "البيانات التي تم تحليلها",
    cancelPayment: "إلغاء الدفع",
    continueAction: "متابعة",
    checksTraditional: [
      "استرجاع سياق الحساب من JOFS",
      "فحص المستفيد والتاجر",
      "تحليل سمعة الموقع",
      "مقارنة الجهاز والموقع",
      "احتساب إشارات الاحتيال السلوكية",
      "إنشاء تفسير واضح للمستخدم"
    ],
    checksWeb3: [
      "قراءة سياق المعاملة على البلوكشين",
      "فحص سمعة المحفظة",
      "التحقق من العقد الذكي",
      "تحليل صلاحيات الرموز",
      "تتبع علاقات المحافظ المشبوهة",
      "إنشاء تفسير واضح للمستخدم"
    ],
    completedSafe: "اكتملت رحلة الدفع في وضع العرض.",
    completedBlocked: "تم إلغاء الدفع قبل الموافقة.",
    error: "تعذر إكمال التقييم. يرجى المحاولة مرة أخرى."
  }
};

const $ = (id) => document.getElementById(id);
const t = (key) => translations[state.language][key] ?? key;

async function initialize() {
  const response = await fetch("/api/demo/scenarios");
  state.scenarios = await response.json();
  bindEvents();
  await loadJofsMode();
  await loadLiveAccounts();
  switchDataSource("live");
  populateWeb3("safe");
  applyTranslations();
}

function bindEvents() {
  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => switchTab(button.dataset.tab));
  });
  $("languageToggle").addEventListener("click", toggleLanguage);
  $("sourceLive").addEventListener("change", () => switchDataSource("live"));
  $("sourceDemo").addEventListener("change", () => switchDataSource("demo"));
  $("liveAccountSelect").addEventListener("change", (event) => onLiveAccountChange(event.target.value));
  $("liveBeneficiarySelect").addEventListener("change", (event) => onLiveBeneficiaryChange(event.target.value));
  $("traditionalScenario").addEventListener("change", (event) => populateTraditional(event.target.value));
  $("web3Scenario").addEventListener("change", (event) => populateWeb3(event.target.value));
  $("confirmTraditional").addEventListener("click", () => runAssessment("traditional"));
  $("confirmWeb3").addEventListener("click", () => runAssessment("web3"));
  $("modalClose").addEventListener("click", closeModal);
  $("cancelAction").addEventListener("click", () => finishDemo(false));
  $("continueAction").addEventListener("click", () => finishDemo(true));
}

async function loadJofsMode() {
  try {
    const response = await fetch("/api/health");
    const health = await response.json();
    state.jofsMode = health.jofs_mode;
  } catch (error) {
    state.jofsMode = "unknown";
  }
  $("jofsModePill").textContent = `JOFS: ${state.jofsMode}`;
}

function switchDataSource(mode) {
  state.dataSource = mode;
  $("sourceLive").checked = mode === "live";
  $("sourceDemo").checked = mode === "demo";
  $("liveSourceBlock").classList.toggle("hidden", mode !== "live");
  $("demoSourceBlock").classList.toggle("hidden", mode !== "demo");
  $("merchant").readOnly = mode === "demo";
  $("domain").readOnly = mode === "demo";

  if (mode === "demo") {
    populateTraditional($("traditionalScenario").value);
  } else if (state.liveAccounts.length > 0) {
    onLiveAccountChange($("liveAccountSelect").value);
  }
}

async function loadLiveAccounts() {
  try {
    const response = await fetch("/api/jofs/accounts");
    state.liveAccounts = await response.json();
  } catch (error) {
    console.error(error);
    state.liveAccounts = [];
  }

  $("liveAccountSelect").innerHTML = state.liveAccounts
    .map((account) => {
      const id = account.id || account.accountId;
      return `<option value="${id}">${account.name || id}</option>`;
    })
    .join("");

  if (state.liveAccounts.length > 0) {
    await onLiveAccountChange($("liveAccountSelect").value);
  }
}

async function onLiveAccountChange(accountId) {
  const account = state.liveAccounts.find((a) => (a.id || a.accountId) === accountId);
  $("accountName").textContent = account ? account.name || accountId : accountId;
  $("accountIban").textContent = (account && account.masked_iban) || "";
  $("accountBalance").textContent = "…";

  if (account) {
    $("merchant").value = $("merchant").value || "";
    $("domain").value = $("domain").value || "";
  }

  try {
    const response = await fetch(`/api/jofs/accounts/${accountId}/balance`);
    const balance = await response.json();
    $("accountBalance").textContent = `${Number(balance.available_balance).toFixed(2)} ${balance.currency}`;
    if (!$("amount").value) $("amount").value = Math.min(50, balance.available_balance);
  } catch (error) {
    $("accountBalance").textContent = "—";
  }

  try {
    const response = await fetch(`/api/jofs/accounts/${accountId}/beneficiaries`);
    state.liveBeneficiaries = await response.json();
  } catch (error) {
    state.liveBeneficiaries = [];
  }

  $("liveBeneficiarySelect").innerHTML = state.liveBeneficiaries
    .map((beneficiary) => {
      const id = beneficiary.id || beneficiary.beneficiaryId;
      return `<option value="${id}">${beneficiary.name || id}</option>`;
    })
    .join("");

  if (state.liveBeneficiaries.length > 0) {
    onLiveBeneficiaryChange($("liveBeneficiarySelect").value);
  } else {
    $("beneficiary").value = "";
  }
}

function onLiveBeneficiaryChange(beneficiaryId) {
  const beneficiary = state.liveBeneficiaries.find((b) => (b.id || b.beneficiaryId) === beneficiaryId);
  $("beneficiary").value = beneficiary ? beneficiary.name || beneficiaryId : "";
  if (beneficiary && !$("merchant").value) {
    $("merchant").value = beneficiary.name || "";
  }
}

function switchTab(tabName) {
  state.paymentType = tabName;
  document.querySelectorAll(".tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === tabName));
  $("traditionalPanel").classList.toggle("active", tabName === "traditional");
  $("web3Panel").classList.toggle("active", tabName === "web3");
}

function toggleLanguage() {
  state.language = state.language === "en" ? "ar" : "en";
  document.documentElement.lang = state.language;
  document.documentElement.dir = state.language === "ar" ? "rtl" : "ltr";
  $("languageToggle").textContent = state.language === "en" ? "العربية" : "English";
  applyTranslations();
  populateWeb3($("web3Scenario").value);
}

function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    const value = t(key);
    if (typeof value === "string") element.textContent = value;
  });
}

function populateTraditional(key) {
  const scenario = state.scenarios.traditional[key];
  $("beneficiary").value = key === "safe" ? "Noon Jordan" : "Fast Visa Approval";
  $("merchant").value = scenario.merchant;
  $("amount").value = scenario.amount;
  $("domain").value = scenario.domain;
}

function populateWeb3(key) {
  const scenario = state.scenarios.web3[key];
  $("contractAddress").value = scenario.contract_address;
  $("tokenSymbol").value = scenario.token_symbol;
  $("approvalLimit").value = scenario.approval_limit === "unlimited" ? t("unlimited") : t("limited");
}

function buildRequest(type) {
  if (type === "traditional") {
    if (state.dataSource === "demo") {
      const key = $("traditionalScenario").value;
      const scenario = state.scenarios.traditional[key];

      return {
        ...scenario,
        amount: Number($("amount").value),
        merchant: $("merchant").value.trim(),
        domain: $("domain").value.trim(),
      };
    }

    // Live JOFS account: the backend resolves account/balance/beneficiary/
    // transaction-history via JOFS itself -- this just identifies which
    // account/beneficiary to assess.
    const accountId = $("liveAccountSelect").value;
    const beneficiaryId = $("liveBeneficiarySelect").value;

    return {
      account_id: accountId,
      beneficiary_id: beneficiaryId,
      amount: Number($("amount").value),
      currency: "JOD",
      merchant: $("merchant").value.trim() || $("beneficiary").value.trim(),
      domain: $("domain").value.trim() || "unspecified",
      device_id: `BROWSER-${accountId}`,
      location: "Amman",
      rapid_attempts: 0,
    };
  }

  return { ...state.scenarios.web3[$("web3Scenario").value] };
}

async function runAssessment(type) {
  state.paymentType = type;
  resetModal();
  $("analysisModal").classList.remove("hidden");
  document.body.style.overflow = "hidden";

  const checks = type === "traditional" ? t("checksTraditional") : t("checksWeb3");
  renderChecks(checks);
  const animationPromise = animateChecks(checks.length);

  try {
    const responsePromise = fetch(`/api/risk/${type}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildRequest(type)),
    }).then(async (response) => {
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    });

    const [assessment] = await Promise.all([responsePromise, animationPromise]);
    state.assessment = assessment;
    showResult(assessment);
  } catch (error) {
    console.error(error);
    await animationPromise;
    showError();
  }
}

function resetModal() {
  const modal = document.querySelector(".analysis-modal");
  modal.classList.remove("low", "review", "high");
  $("analysisState").classList.remove("hidden");
  $("resultState").classList.add("hidden");
  $("modalClose").classList.add("hidden");
  $("progressBar").style.width = "0%";
}

function renderChecks(checks) {
  $("checkList").innerHTML = checks.map((check, index) => `<div class="check-item" data-check="${index}">${check}</div>`).join("");
}

async function animateChecks(count) {
  for (let index = 0; index < count; index += 1) {
    const item = document.querySelector(`[data-check="${index}"]`);
    item.classList.add("active");
    $("progressBar").style.width = `${Math.round(((index + 1) / count) * 100)}%`;
    await delay(360);
    item.classList.add("complete");
  }
  await delay(300);
}

function showResult(assessment) {
  const modal = document.querySelector(".analysis-modal");
  modal.classList.add(assessment.risk_level);
  $("analysisState").classList.add("hidden");
  $("resultState").classList.remove("hidden");
  $("modalClose").classList.remove("hidden");
  $("resultIcon").textContent = assessment.risk_level === "low" ? "✓" : assessment.risk_level === "review" ? "?" : "!";
  $("resultVerdict").textContent = state.language === "ar" ? assessment.verdict_ar : assessment.verdict_en;
  $("resultSummary").textContent = state.language === "ar" ? assessment.summary_ar : assessment.summary_en;
  animateScore(assessment.risk_score);

  $("factorList").innerHTML = assessment.factors
    .map((factor) => `<li>${state.language === "ar" ? factor.message_ar : factor.message_en}</li>`)
    .join("");
  const dataSources = [...assessment.data_sources];
  if (assessment.account_balance !== null && assessment.account_balance !== undefined) {
    dataSources.push(`Available balance: ${Number(assessment.account_balance).toFixed(2)}`);
  }
  if (assessment.funds_available !== null && assessment.funds_available !== undefined) {
    dataSources.push(`Funds confirmation: ${assessment.funds_available ? "available" : "insufficient"}`);
  }
  if (assessment.beneficiary_verified !== null && assessment.beneficiary_verified !== undefined) {
    dataSources.push(`Beneficiary verified: ${assessment.beneficiary_verified ? "yes" : "no"}`);
  }
  $("dataSourceList").innerHTML = dataSources.map((source) => `<li>${source}</li>`).join("");
  $("prototypeNotice").textContent = assessment.prototype_notice;

  const continueButton = $("continueAction");
  const cancelButton = $("cancelAction");
  if (assessment.recommendation === "cancel") {
    continueButton.style.opacity = ".55";
    cancelButton.classList.add("danger-action");
  } else {
    continueButton.style.opacity = "1";
    cancelButton.classList.remove("danger-action");
  }
}

function showError() {
  $("analysisState").classList.add("hidden");
  $("resultState").classList.remove("hidden");
  $("modalClose").classList.remove("hidden");
  $("resultVerdict").textContent = t("error");
  $("resultSummary").textContent = "";
  $("riskScore").textContent = "--";
  $("factorList").innerHTML = "";
  $("dataSourceList").innerHTML = "";
  $("prototypeNotice").textContent = "";
}

function animateScore(target) {
  let current = 0;
  const increment = Math.max(1, Math.ceil(target / 30));
  const timer = setInterval(() => {
    current = Math.min(target, current + increment);
    $("riskScore").textContent = current;
    if (current >= target) clearInterval(timer);
  }, 26);
}

function finishDemo(continuePayment) {
  const message = continuePayment ? t("completedSafe") : t("completedBlocked");
  closeModal();
  showToast(message);
}

function closeModal() {
  $("analysisModal").classList.add("hidden");
  document.body.style.overflow = "";
}

function showToast(message) {
  const toast = document.createElement("div");
  toast.className = "toast-message";
  toast.textContent = message;
  Object.assign(toast.style, {
    position: "fixed",
    insetInlineEnd: "24px",
    bottom: "24px",
    zIndex: "200",
    padding: "13px 16px",
    borderRadius: "12px",
    background: "#11243e",
    color: "#eef5ff",
    border: "1px solid rgba(84,167,255,.28)",
    boxShadow: "0 18px 55px rgba(0,0,0,.4)",
  });
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2600);
}

const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

initialize().catch((error) => {
  console.error(error);
  document.body.innerHTML = `<main style="padding:40px;color:white">${translations.en.error}</main>`;
});
