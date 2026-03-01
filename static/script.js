const uploadBtn = document.getElementById("uploadBtn");
const fileInput = document.getElementById("fileInput");
const statusBox = document.getElementById("statusBox");
const resultJson = document.getElementById("resultJson");
const useGenCheckbox = document.getElementById("useGen");

function setStatus(s) {
  statusBox.innerText = "Status: " + s;
}

uploadBtn.onclick = async () => {

  const f = fileInput.files[0];
  if (!f) {
    alert("Select a file first");
    return;
  }

  try {

    // 1️⃣ Request signed URL
    setStatus("Requesting upload URL...");
    const resp = await fetch("/api/request-upload", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filename: f.name,
        content_type: f.type   // MUST match actual file type
      })
    });

    const j = await resp.json();
    const upload_url = j.upload_url;
    const asset_key = j.asset_key;

    // 2️⃣ Upload directly with correct Content-Type
    setStatus("Uploading to signed URL...");

    await fetch(upload_url, {
      method: "PUT",
      headers: {
        "Content-Type": f.type   // REQUIRED per Presaige docs
      },
      body: f
    });

    // 3️⃣ Analyze
    setStatus("Analyzing...");
    const analyzeResp = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        asset_key: asset_key,
        use_generate: useGenCheckbox.checked
      })
    });

    const results = await analyzeResp.json();

    setStatus("Complete ✅");
    resultJson.innerHTML =
      "<pre>" + JSON.stringify(results, null, 2) + "</pre>";

  } catch (err) {
    console.error(err);
    alert("Upload failed. Check console.");
  }
};