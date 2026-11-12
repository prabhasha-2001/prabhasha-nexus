function resolveApiBase() {
  if (window.PRABHASHA_API_BASE) return window.PRABHASHA_API_BASE;
  if (window.location.protocol === "file:") return "http://localhost:5000/api/v1";
  if (["5000", "5500", "8000", "3000", "5173"].includes(window.location.port)) {
    return window.location.port === "5000" ? "/api/v1" : "http://localhost:5000/api/v1";
  }
  return "/api/v1";
}

window.PRABHASHA_CONFIG = {
  apiBase: resolveApiBase(),
  siteName: "Prabhasha Nexus",
  ownerFallback: {
    full_name: "Muwagamage Tharushi Prabhasha Dilshani",
    professional_title: "AI/ML Engineer · Data Science Enthusiast · Python Developer",
    summary:
      "Final-year Information Technology undergraduate focused on AI/ML, data science and intelligent software development.",
    email: "mtprabhashadilshani2001@gmail.com",
    location: "Kaduwela, Sri Lanka",
    github_url: "https://github.com/prabhasha-2001",
    linkedin_url: "https://linkedin.com/in/prabhasha-dilshani-7258593a6"
  }
};
