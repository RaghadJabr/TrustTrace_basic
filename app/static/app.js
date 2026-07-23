"use strict";

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const error = await response.json();
      message = error.detail || message;
    } catch {
      // The response did not contain JSON.
    }

    throw new Error(message);
  }

  return response.json();
}

async function loadLiveAccountContext(accountId = "1001") {
  const [account, balance, beneficiaries, transactions] = await Promise.all([
    fetchJson(`/api/jofs/accounts/${encodeURIComponent(accountId)}`),
    fetchJson(`/api/jofs/accounts/${encodeURIComponent(accountId)}/balance`),
    fetchJson(`/api/jofs/accounts/${encodeURIComponent(accountId)}/beneficiaries`),
    fetchJson(`/api/jofs/accounts/${encodeURIComponent(accountId)}/transactions`),
  ]);

  const availableBalance =
    balance.available_balance ??
    balance.availableBalance?.balanceAmount ??
    0;

  const currency =
    balance.currency ??
    balance.balanceCurrency ??
    account.accountCurrency ??
    account.currency ??
    "JOD";

  const iban =
    account.mainRoute?.address ??
    account.masked_iban ??
    account.accountId ??
    account.id ??
    accountId;

  return {
    accountId: getAccountId(account) || accountId,
    accountName: getAccountName(account) || `Account ${accountId}`,
    iban,
    availableBalance: Number(availableBalance ?? 0),
    currency,
    beneficiaries: Array.isArray(beneficiaries) ? beneficiaries : [],
    transactions: Array.isArray(transactions) ? transactions : [],
    rawAccount: account,
    rawBalance: balance,
  };
}

const state = {
  language: "en",
  scenarios: null,
  liveAccount: null,
  assessment: null,
  paymentType: "traditional",
  dataSource: "live",
  jofsMode: null,
  liveAccounts: [],
  liveBeneficiaries: [],
  liveTransactions: [],
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

function bindIfPresent(id, eventName, handler) {
  const element = $(id);
  if (element) element.addEventListener(eventName, handler);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getAccountId(account) {
  return String(account?.accountId ?? account?.id ?? "");
}

function getAccountName(account) {
  return (
    account?.accountOwner?.name?.enName ??
    account?.accountName ??
    account?.name ??
    ""
  );
}

function getAccountIban(account) {
  return (
    account?.mainRoute?.address ??
    account?.masked_iban ??
    account?.accountId ??
    account?.id ??
    ""
  );
}

function getBeneficiaryId(beneficiary) {
  return String(
    beneficiary?.beneficiaryId ??
    beneficiary?.id ??
    ""
  );
}

function getBeneficiaryName(beneficiary) {
  return (
    beneficiary?.beneficiaryNickname ??
    beneficiary?.beneficiaryName?.tradeName?.enName ??
    beneficiary?.beneficiaryName?.enName ??
    beneficiary?.name ??
    ""
  );
}

function maskIban(value) {
  const compact = String(value ?? "").replace(/\s+/g, "");

  if (compact.length <= 8) {
    return compact || "Unavailable";
  }

  return `${compact.slice(0, 4)} **** **** ${compact.slice(-4)}`;
}

function formatMoney(amount, currency) {
  const numericAmount = Number(amount ?? 0);
  const safeAmount = Number.isFinite(numericAmount) ? numericAmount : 0;

  return `${safeAmount.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${currency || "JOD"}`;
}

async function initialize() {
  state.scenarios = await fetchJson("/api/demo/scenarios");

  bindEvents();
  await loadJofsMode();
  await loadLiveAccounts();

  const demoSelected = $("sourceDemo")?.checked === true;
  switchDataSource(demoSelected ? "demo" : "live");

  populateWeb3("safe");
  applyTranslations();
}

function bindEvents() {
  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => switchTab(button.dataset.tab));
  });

  bindIfPresent("languageToggle", "click", toggleLanguage);
  bindIfPresent("sourceLive", "change", () => switchDataSource("live"));
  bindIfPresent("sourceDemo", "change", () => switchDataSource("demo"));
  bindIfPresent("liveAccountSelect", "change", (event) => {
    void onLiveAccountChange(event.target.value);
  });
  bindIfPresent("liveBeneficiarySelect", "change", (event) => {
    onLiveBeneficiaryChange(event.target.value);
  });
  bindIfPresent("traditionalScenario", "change", (event) => {
    populateTraditional(event.target.value);
  });
  bindIfPresent("web3Scenario", "change", (event) => {
    populateWeb3(event.target.value);
  });
  bindIfPresent("confirmTraditional", "click", () => runAssessment("traditional"));
  bindIfPresent("confirmWeb3", "click", () => runAssessment("web3"));
  bindIfPresent("modalClose", "click", closeModal);
  bindIfPresent("cancelAction", "click", () => finishDemo(false));
  bindIfPresent("continueAction", "click", () => finishDemo(true));
}

async function loadJofsMode() {
  try {
    const health = await fetchJson("/api/health");
    state.jofsMode = health.jofs_mode ?? "unknown";
  } catch (error) {
    console.error("Could not load JOFS mode:", error);
    state.jofsMode = "unknown";
  }

  const modePill = $("jofsModePill");
  if (modePill) modePill.textContent = `JOFS: ${state.jofsMode}`;
}

function switchDataSource(mode) {
  state.dataSource = mode;

  if ($("sourceLive")) $("sourceLive").checked = mode === "live";
  if ($("sourceDemo")) $("sourceDemo").checked = mode === "demo";
  if ($("liveSourceBlock")) $("liveSourceBlock").classList.toggle("hidden", mode !== "live");
  if ($("demoSourceBlock")) $("demoSourceBlock").classList.toggle("hidden", mode !== "demo");
  if ($("merchant")) $("merchant").readOnly = mode === "demo";
  if ($("domain")) $("domain").readOnly = mode === "demo";

  if (mode === "demo") {
    populateTraditional($("traditionalScenario")?.value || "safe");
    return;
  }

  const selectedAccountId =
    $("liveAccountSelect")?.value ||
    state.liveAccount?.accountId ||
    getAccountId(state.liveAccounts[0]);

  if (selectedAccountId) {
    void onLiveAccountChange(selectedAccountId);
  } else {
    renderLiveAccount();
    populateTraditional($("traditionalScenario")?.value || "safe");
  }
}

async function loadLiveAccounts() {
  try {
    const accounts = await fetchJson("/api/jofs/accounts");
    state.liveAccounts = Array.isArray(accounts) ? accounts : [];
  } catch (error) {
    console.error("Could not load JOFS accounts:", error);
    state.liveAccounts = [];
  }

  const accountSelect = $("liveAccountSelect");
  if (accountSelect) {
    accountSelect.innerHTML = state.liveAccounts
      .map((account) => {
        const id = getAccountId(account);
        const label = getAccountName(account) || `Account ${id}`;
        return `<option value="${escapeHtml(id)}">${escapeHtml(label)}</option>`;
      })
      .join("");
  }

  if (state.liveAccounts.length === 0) {
    return;
  }

  const initialAccountId = accountSelect?.value || getAccountId(state.liveAccounts[0]);
  if (initialAccountId) await onLiveAccountChange(initialAccountId);
}

async function onLiveAccountChange(accountId) {
  if (!accountId) return;

  const accountSummary = state.liveAccounts.find(
    (account) => getAccountId(account) === String(accountId),
  );

  if ($("accountName")) {
    $("accountName").textContent =
      getAccountName(accountSummary) || `Account ${accountId}`;
  }
  if ($("accountIban")) {
    $("accountIban").textContent = maskIban(getAccountIban(accountSummary) || accountId);
  }
  if ($("accountBalance")) $("accountBalance").textContent = "…";

  try {
    const context = await loadLiveAccountContext(accountId);
    state.liveAccount = context;
    state.liveBeneficiaries = context.beneficiaries;
    state.liveTransactions = context.transactions;
    renderLiveAccount();
  } catch (error) {
    console.error("Could not load JOFS account context:", error);
    state.liveAccount = accountSummary
      ? {
          accountId,
          accountName: getAccountName(accountSummary) || `Account ${accountId}`,
          iban: getAccountIban(accountSummary) || accountId,
          availableBalance: 0,
          currency: accountSummary.accountCurrency || accountSummary.currency || "JOD",
          beneficiaries: [],
          transactions: [],
          rawAccount: accountSummary,
          rawBalance: null,
        }
      : null;
    state.liveBeneficiaries = [];
    state.liveTransactions = [];
    renderLiveAccount();
  }

  const beneficiarySelect = $("liveBeneficiarySelect");
  if (beneficiarySelect) {
    beneficiarySelect.innerHTML = state.liveBeneficiaries
      .map((beneficiary) => {
        const id = getBeneficiaryId(beneficiary);
        const label = getBeneficiaryName(beneficiary) || `Beneficiary ${id}`;
        return `<option value="${escapeHtml(id)}">${escapeHtml(label)}</option>`;
      })
      .join("");
  }

  const initialBeneficiaryId =
    beneficiarySelect?.value ||
    getBeneficiaryId(state.liveBeneficiaries[0]);

  if (initialBeneficiaryId) {
    onLiveBeneficiaryChange(initialBeneficiaryId);
  } else if ($("beneficiary")) {
    $("beneficiary").value = "";
  }

  const amountInput = $("amount");
  if (amountInput && !amountInput.value) {
    const available = Number(state.liveAccount?.availableBalance ?? 0);
    amountInput.value = available > 0 ? Math.min(50, available) : 50;
  }

  populateTraditional($("traditionalScenario")?.value || "safe");
}

function renderLiveAccount() {
  if (!state.liveAccount) return;

  if ($("accountName")) {
    $("accountName").textContent =
      state.liveAccount.accountName ||
      `Account ${state.liveAccount.accountId}`;
  }

  if ($("accountIban")) {
    $("accountIban").textContent = maskIban(state.liveAccount.iban);
  }

  if ($("accountBalance")) {
    $("accountBalance").textContent = formatMoney(
      state.liveAccount.availableBalance,
      state.liveAccount.currency,
    );
  }
}

function onLiveBeneficiaryChange(beneficiaryId) {
  const beneficiary = state.liveBeneficiaries.find(
    (item) => getBeneficiaryId(item) === String(beneficiaryId),
  );

  const name = getBeneficiaryName(beneficiary) || beneficiaryId || "";
  if ($("beneficiary")) $("beneficiary").value = name;

  if (beneficiary && $("merchant") && !$("merchant").value) {
    $("merchant").value = name;
  }
}

function switchTab(tabName) {
  state.paymentType = tabName;
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === tabName);
  });
  if ($("traditionalPanel")) $("traditionalPanel").classList.toggle("active", tabName === "traditional");
  if ($("web3Panel")) $("web3Panel").classList.toggle("active", tabName === "web3");
}

function toggleLanguage() {
  state.language = state.language === "en" ? "ar" : "en";
  document.documentElement.lang = state.language;
  document.documentElement.dir = state.language === "ar" ? "rtl" : "ltr";
  if ($("languageToggle")) {
    $("languageToggle").textContent = state.language === "en" ? "العربية" : "English";
  }
  applyTranslations();
  populateWeb3($("web3Scenario")?.value || "safe");
}

function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    const value = t(key);
    if (typeof value === "string") element.textContent = value;
  });
}

function populateTraditional(key) {
  const scenario = state.scenarios?.traditional?.[key];
  if (!scenario) return;

  if (state.dataSource === "demo") {
    if ($("beneficiary")) {
      $("beneficiary").value = key === "safe" ? "Noon Jordan" : "Fast Visa Approval";
    }
  } else {
    const selectedBeneficiaryId =
      $("liveBeneficiarySelect")?.value ||
      getBeneficiaryId(state.liveBeneficiaries[0]);

    const liveBeneficiary = state.liveBeneficiaries.find(
      (beneficiary) => getBeneficiaryId(beneficiary) === String(selectedBeneficiaryId),
    );

    if ($("beneficiary")) {
      $("beneficiary").value =
        getBeneficiaryName(liveBeneficiary) ||
        scenario.merchant;
    }
  }

  if ($("merchant")) $("merchant").value = scenario.merchant;
  if ($("amount")) $("amount").value = scenario.amount;
  if ($("domain")) $("domain").value = scenario.domain;
}

function populateWeb3(key) {
  const scenario = state.scenarios?.web3?.[key];
  if (!scenario) return;

  if ($("contractAddress")) $("contractAddress").value = scenario.contract_address;
  if ($("tokenSymbol")) $("tokenSymbol").value = scenario.token_symbol;
  if ($("approvalLimit")) {
    $("approvalLimit").value =
      scenario.approval_limit === "unlimited"
        ? t("unlimited")
        : t("limited");
  }
}

function buildRequest(type) {
  if (type === "traditional") {
    const scenarioKey = $("traditionalScenario")?.value || "safe";
    const scenario = state.scenarios.traditional[scenarioKey];

    if (state.dataSource === "demo") {
      return {
        ...scenario,
        amount: Number($("amount")?.value ?? scenario.amount),
        merchant: $("merchant")?.value.trim() || scenario.merchant,
        domain: $("domain")?.value.trim() || scenario.domain,
      };
    }

    const accountId =
      $("liveAccountSelect")?.value ||
      state.liveAccount?.accountId ||
      scenario.account_id;

    const beneficiaryId =
      $("liveBeneficiarySelect")?.value ||
      getBeneficiaryId(state.liveBeneficiaries[0]) ||
      scenario.beneficiary_id;

    return {
      account_id: accountId,
      beneficiary_id: beneficiaryId,
      amount: Number($("amount")?.value ?? scenario.amount),
      currency: state.liveAccount?.currency || scenario.currency || "JOD",
      merchant: $("merchant")?.value.trim() || $("beneficiary")?.value.trim() || scenario.merchant,
      domain: $("domain")?.value.trim() || scenario.domain || "unspecified",
      device_id: `BROWSER-${accountId}`,
      location: scenario.location || "Amman",
      rapid_attempts: Number(scenario.rapid_attempts ?? 0),
    };
  }

  const web3Key = $("web3Scenario")?.value || "safe";
  return { ...state.scenarios.web3[web3Key] };
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
    const responsePromise = fetchJson(`/api/risk/${type}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildRequest(type)),
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
  $("checkList").innerHTML = checks
    .map((check, index) => `<div class="check-item" data-check="${index}">${escapeHtml(check)}</div>`)
    .join("");
}

async function animateChecks(count) {
  for (let index = 0; index < count; index += 1) {
    const item = document.querySelector(`[data-check="${index}"]`);
    if (!item) continue;
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
  $("resultIcon").textContent =
    assessment.risk_level === "low"
      ? "✓"
      : assessment.risk_level === "review"
        ? "?"
        : "!";
  $("resultVerdict").textContent =
    state.language === "ar" ? assessment.verdict_ar : assessment.verdict_en;
  $("resultSummary").textContent =
    state.language === "ar" ? assessment.summary_ar : assessment.summary_en;
  animateScore(assessment.risk_score);

  $("factorList").innerHTML = assessment.factors
    .map((factor) => {
      const message = state.language === "ar" ? factor.message_ar : factor.message_en;
      return `<li>${escapeHtml(message)}</li>`;
    })
    .join("");

  const dataSources = [...(assessment.data_sources || [])];
  if (assessment.account_balance !== null && assessment.account_balance !== undefined) {
    dataSources.push(`Available balance: ${Number(assessment.account_balance).toFixed(2)}`);
  }
  if (assessment.funds_available !== null && assessment.funds_available !== undefined) {
    dataSources.push(
      `Funds confirmation: ${assessment.funds_available ? "available" : "insufficient"}`,
    );
  }
  if (assessment.beneficiary_verified !== null && assessment.beneficiary_verified !== undefined) {
    dataSources.push(
      `Beneficiary verified: ${assessment.beneficiary_verified ? "yes" : "no"}`,
    );
  }

  $("dataSourceList").innerHTML = dataSources
    .map((source) => `<li>${escapeHtml(source)}</li>`)
    .join("");
  $("prototypeNotice").textContent = assessment.prototype_notice || "";

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
  const numericTarget = Number(target ?? 0);
  const increment = Math.max(1, Math.ceil(numericTarget / 30));
  const timer = setInterval(() => {
    current = Math.min(numericTarget, current + increment);
    $("riskScore").textContent = current;
    if (current >= numericTarget) clearInterval(timer);
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
  document.body.innerHTML = `<main style="padding:40px;color:white">${escapeHtml(translations.en.error)}</main>`;
});