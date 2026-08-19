# Portfolio Deploy Karne Ka Tareeqa

**File:** `index.html` — ek hi file, koi build nahi, koi dependency nahi.

---

## ⚠️ Pehle 3 cheezein badlo

`index.html` kholo aur ye placeholders replace karo (Ctrl+H se find-replace):

| Dhoondo | Kis se badlo |
|---|---|
| `YOUR.EMAIL@gmail.com` | Tumhara professional email |
| `YOUR-HANDLE` | LinkedIn username |

**Placeholder chhoda to bahut bura lagta hai** — bilkul waise hi jaise `PhoneCam-Pro` mein `yourusername` reh gaya tha. Deploy se pehle zaroor check karo.

LinkedIn abhi nahi hai? To LinkedIn wale dono blocks **delete kar do** (hero ka button + contact card). Khali link se koi link na hona behtar hai.

---

## Deploy — GitHub Pages (free, 3 minute)

### Tareeqa 1 — Website ka apna repo (recommended)

```bash
# naya folder
mkdir abdullah-portfolio && cd abdullah-portfolio
# index.html yahan copy karo, phir:
git init
git add index.html
git commit -m "feat: portfolio site"
git branch -M main
git remote add origin https://github.com/ABDULLAH-AMJID/ABDULLAH-AMJID.github.io.git
git push -u origin main
```

Repo ka naam **bilkul yehi** hona chahiye: `ABDULLAH-AMJID.github.io`

Phir: repo → **Settings** → **Pages** → Source: `main` → **Save**

**1–2 minute mein live:** `https://abdullah-amjid.github.io`

> Ye sabse achhi URL hai — chhoti, saaf, CV par accha lagti hai.

### Tareeqa 2 — Profile README repo ke andar

Agar alag repo nahi banana:

1. `ABDULLAH-AMJID/ABDULLAH-AMJID` repo mein `index.html` upload karo
2. Settings → Pages → Source: `main` → Save
3. Live: `https://abdullah-amjid.github.io/ABDULLAH-AMJID`

URL lambi hai, isliye Tareeqa 1 behtar hai.

---

## Deploy ke baad — ye zaroor karo

- [ ] **GitHub profile mein website link lagao**
      Settings → Profile → Website → `https://abdullah-amjid.github.io`
      *(abhi khali hai — ye field muft ki credibility hai)*
- [ ] **Profile README mein link add karo**
- [ ] **CV mein link dalo** — email ke bilkul saath
- [ ] **LinkedIn** → Contact info → Website

---

## Is site mein kya khaas hai

**Scholarship ke liye:**
- "Research & Interests" section hai — universities isi ko dekhti hain. Isme tumhara kaam *research direction* ki tarah pesh kiya gaya hai (real-time systems, safe systems design), na ke sirf projects ki list
- Education section coursework ko projects se jorta hai
- Graduate study ka zikr saaf likha hai

**Internship ke liye:**
- Har project ke saath **engineering detail** hai — "jitter buffer", "shared memory IPC", "DirectShow filter". Recruiter skim karta hai, technical banda ruk ke padhta hai
- Skills 5 categories mein — languages, systems, backend, frontend, practices

**Technical:**
- **Ek hi file**, ~29 KB, koi framework nahi. Footer mein likha hai "no framework, single file" — ye khud ek skill signal hai
- **Dark/light toggle**, choice yaad rakhta hai
- **Print → PDF ready**: Ctrl+P karo to saaf CV-jaisa PDF banta hai. Applications ke liye bohat kaam ka
- Mobile par bhi sahi chalta hai
- Koi tracking, koi external font, koi CDN — offline bhi khulta hai

---

## Aage jab update karna ho

Naya project add karna ho to `index.html` mein `<article class="card">` copy karke naya bana lo. Structure:

```html
<article class="card">
  <div class="card-top">
    <h3><a href="GITHUB_LINK" target="_blank" rel="noopener">Project Name</a></h3>
    <span class="flag">Category</span>
  </div>
  <div class="role">Ek line mein kya hai</div>
  <p>Kya karta hai aur <strong>kis ke liye</strong> hai.</p>
  <p class="detail">Technical detail — kaise banaya, kya mushkil tha.</p>
  <div class="tags">
    <span class="tag">Tech</span><span class="tag">Tech</span>
  </div>
</article>
```

**Projects ko strongest-first rakhna.** Abhi order hai: PhoneCam Pro → SpaceMedic → EarBridge → Publisher → Vortex → Sharp Pixel. Jab koi behtar project bane, use upar le aana.
