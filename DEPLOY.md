# Host Stockroom on Render (free)

This gives you a public link like `https://stockroom-inventory.onrender.com` that
anyone can open — no login, no install. Everyone shares the same data.

## Step 1 — Put the code on GitHub
1. Go to https://github.com and create a free account if you don't have one.
2. Click **New repository** → name it `stockroom` → Create repository.
3. On your computer, unzip this project, then upload it:
   - Easiest way: on the new repo's page, click **uploading an existing file**,
     drag in all the files/folders from this project, and commit.

## Step 2 — Create a Render account
1. Go to https://render.com and sign up (you can sign up with your GitHub account —
   this makes step 3 easier).

## Step 3 — Deploy
1. In Render, click **New** → **Blueprint**.
2. Connect your GitHub account if asked, then select the `stockroom` repo.
3. Render will read the `render.yaml` file in this project automatically and
   set everything up — web service, disk for your data, and a secret key.
4. Click **Apply** / **Create**.
5. Wait 2–3 minutes for the first build to finish.

## Step 4 — You're live
Render gives you a URL like:

```
https://stockroom-inventory.onrender.com
```

Share that link with anyone — staff, phone, laptop, doesn't matter. Everyone sees
the same products and stock.

## Notes
- **Free tier sleeps** after 15 minutes of no traffic. The first visit after that
  takes ~30–50 seconds to "wake up" — normal for free hosting, not a bug.
- Your data lives on the small disk Render attaches (`stockroom-data`), so it
  survives restarts and redeploys.
- If you ever want a custom domain (e.g. `inventory.yourshop.lk`), Render lets
  you add that for free under **Settings → Custom Domains** once deployed.
- To update the app later: change the code on GitHub, Render auto-redeploys.

## If Blueprint deploy isn't available on your plan
You can set it up manually instead:
1. **New** → **Web Service** → connect the `stockroom` repo.
2. **Build command:** `pip install -r requirements.txt`
3. **Start command:** `gunicorn app:app`
4. Add an environment variable: `SECRET_KEY` = any random text.
5. (Optional but recommended) Add a disk under **Disks**, mount path
   `/opt/render/project/src/data`, and add environment variable
   `DATA_DIR` = `/opt/render/project/src/data` so your data survives redeploys.
