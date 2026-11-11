// Shared navigation for the help pages. PAGES is the single list of help pages:
// add a page here (and create the file) and every page's menu picks it up.
// pipeline/check_help.py checks this list against the files in this folder.
const PAGES = [
  ["index.html", "Overview & quick start"],
  ["papers.html", "Paper list & abstract"],
  ["workflow.html", "Workflow panel"],
  ["ranking.html", "How papers are ranked"],
  ["ingestion.html", "Adding papers (ingestion)"],
  ["limitations.html", "Data sources & limitations"],
  ["troubleshooting.html", "Troubleshooting"],
];

(function () {
  const here = location.pathname.split("/").pop() || "index.html";
  const nav = document.getElementById("toc");
  if (nav) {
    const list = document.createElement("ol");
    for (const [file, title] of PAGES) {
      const a = document.createElement("a");
      a.href = file;
      a.textContent = title;
      if (file === here) a.setAttribute("aria-current", "page");
      const li = document.createElement("li");
      li.append(a);
      list.append(li);
    }
    const h = document.createElement("h2");
    h.textContent = "Help topics";
    nav.replaceChildren(h, list);
  }
})();
