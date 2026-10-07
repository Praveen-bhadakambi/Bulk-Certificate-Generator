const form = document.querySelector("#jobForm");
const recipientList = document.querySelector("#recipientList");
const recipientTemplate = document.querySelector("#recipientTemplate");
const addRecipientButton = document.querySelector("#addRecipient");
const pasteToggleButton = document.querySelector("#pasteToggle");
const csvImport = document.querySelector("#csvImport");
const csvInput = document.querySelector("#csvInput");
const importCsvButton = document.querySelector("#importCsv");
const clearCsvButton = document.querySelector("#clearCsv");
const sampleButton = document.querySelector("#sampleButton");
const submitButton = document.querySelector("#submitButton");
const serviceStatus = document.querySelector("#serviceStatus");
const recipientCount = document.querySelector("#recipientCount");
const jobTitle = document.querySelector("#jobTitle");
const jobStatus = document.querySelector("#jobStatus");
const progressLabel = document.querySelector("#progressLabel");
const progressCounts = document.querySelector("#progressCounts");
const progressBar = document.querySelector("#progressBar");
const totalCount = document.querySelector("#totalCount");
const successCount = document.querySelector("#successCount");
const failureCount = document.querySelector("#failureCount");
const certificateList = document.querySelector("#certificateList");

let activeJobId = null;
let pollTimer = null;

const sampleRecipients = [
  { name: "Asha Rao", email: "asha@example.com", custom_message: "Great work" },
  { name: "Dev Kumar", email: "dev@example.com", custom_message: "Outstanding progress" },
];

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

function setServiceStatus(text, mode = "ok") {
  serviceStatus.textContent = text;
  serviceStatus.classList.toggle("muted", mode !== "ok");
}

function formatStatus(value) {
  return value.replaceAll("_", " ");
}

function updateRecipientCount() {
  const count = recipientList.querySelectorAll(".recipient-row").length;
  recipientCount.textContent = `${count} recipient${count === 1 ? "" : "s"}`;
}

function addRecipient(recipient = {}) {
  const node = recipientTemplate.content.firstElementChild.cloneNode(true);
  node.querySelector('[data-field="name"]').value = recipient.name || "";
  node.querySelector('[data-field="email"]').value = recipient.email || "";
  node.querySelector('[data-field="custom_message"]').value = recipient.custom_message || "";
  node.querySelector("[data-remove]").addEventListener("click", () => {
    if (recipientList.querySelectorAll(".recipient-row").length === 1) {
      node.querySelector('[data-field="name"]').value = "";
      node.querySelector('[data-field="email"]').value = "";
      node.querySelector('[data-field="custom_message"]').value = "";
      return;
    }
    node.remove();
    updateRecipientCount();
  });
  recipientList.appendChild(node);
  updateRecipientCount();
}

function parseCsvLine(line) {
  const values = [];
  let current = "";
  let quoted = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];

    if (char === '"' && quoted && next === '"') {
      current += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      values.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }

  values.push(current.trim());
  return values;
}

function importCsvRecipients() {
  const rows = csvInput.value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map(parseCsvLine)
    .filter((row) => row[0] && row[1]);

  if (!rows.length) {
    setServiceStatus("No valid rows", "muted");
    return;
  }

  recipientList.replaceChildren();
  rows.forEach(([name, email, custom_message]) => addRecipient({ name, email, custom_message }));
  setServiceStatus("Recipients imported", "ok");
}

function loadSample() {
  recipientList.replaceChildren();
  sampleRecipients.forEach(addRecipient);
  form.elements.issue_date.value = todayIsoDate();
}

function collectPayload() {
  const recipients = [...recipientList.querySelectorAll(".recipient-row")].map((row) => {
    const message = row.querySelector('[data-field="custom_message"]').value.trim();
    return {
      name: row.querySelector('[data-field="name"]').value.trim(),
      email: row.querySelector('[data-field="email"]').value.trim(),
      custom_message: message || null,
    };
  });

  const eventName = form.elements.event_name.value.trim();
  return {
    course_name: form.elements.course_name.value.trim(),
    issuer_name: form.elements.issuer_name.value.trim(),
    issue_date: form.elements.issue_date.value,
    event_name: eventName || null,
    recipients,
  };
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? "Generating..." : "Generate certificates";
}

function renderStatus(job) {
  jobTitle.textContent = `Job #${job.job_id}`;
  jobStatus.textContent = formatStatus(job.status);
  jobStatus.classList.toggle("muted", job.status === "pending" || job.status === "processing");
  progressLabel.textContent = `${job.progress_percent}%`;
  progressCounts.textContent = `${job.success_count} generated`;
  progressBar.style.width = `${job.progress_percent}%`;
  totalCount.textContent = job.total_count;
  successCount.textContent = job.success_count;
  failureCount.textContent = job.failure_count;

  certificateList.replaceChildren();
  job.certificates.forEach((certificate) => {
    const item = document.createElement("div");
    item.className = "certificate-item";

    const details = document.createElement("div");
    const name = document.createElement("strong");
    const email = document.createElement("span");
    name.textContent = certificate.recipient_name;
    email.textContent = certificate.error_message || certificate.recipient_email;
    details.append(name, email);

    if (certificate.status === "generated") {
      const download = document.createElement("a");
      download.className = "download";
      download.href = `/jobs/${job.job_id}/certificates/${certificate.id}`;
      download.target = "_blank";
      download.rel = "noreferrer";
      download.textContent = "Download";
      item.append(details, download);
    } else {
      const tag = document.createElement("span");
      tag.className = `tag ${certificate.status}`;
      tag.textContent = formatStatus(certificate.status);
      item.append(details, tag);
    }

    certificateList.appendChild(item);
  });
}

async function pollJob(jobId) {
  const response = await fetch(`/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error("Could not load job status.");
  }

  const job = await response.json();
  renderStatus(job);
  const done = ["completed", "completed_with_errors", "failed"].includes(job.status);
  if (done) {
    clearInterval(pollTimer);
    pollTimer = null;
    setLoading(false);
    setServiceStatus(job.status === "failed" ? "Finished with failures" : "Certificates ready", "ok");
  }
  return done;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!form.reportValidity()) {
    return;
  }

  clearInterval(pollTimer);
  setLoading(true);
  setServiceStatus("Submitting", "muted");

  try {
    const response = await fetch("/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectPayload()),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail ? JSON.stringify(error.detail) : "Request failed.");
    }

    const created = await response.json();
    activeJobId = created.job_id;
    setServiceStatus("Processing", "muted");
    const done = await pollJob(activeJobId);
    if (!done) {
      pollTimer = setInterval(() => pollJob(activeJobId).catch(showError), 1000);
    }
  } catch (error) {
    showError(error);
    setLoading(false);
  }
});

function showError(error) {
  clearInterval(pollTimer);
  pollTimer = null;
  setServiceStatus("Error", "muted");
  certificateList.innerHTML = `<div class="empty-state">${error.message}</div>`;
}

addRecipientButton.addEventListener("click", () => addRecipient());
pasteToggleButton.addEventListener("click", () => {
  csvImport.hidden = !csvImport.hidden;
  pasteToggleButton.textContent = csvImport.hidden ? "Paste CSV" : "Hide CSV";
  if (!csvImport.hidden) {
    csvInput.focus();
  }
});
importCsvButton.addEventListener("click", importCsvRecipients);
clearCsvButton.addEventListener("click", () => {
  csvInput.value = "";
  csvInput.focus();
});
sampleButton.addEventListener("click", loadSample);

loadSample();
