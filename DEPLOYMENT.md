# Deployment Guide

Step-by-step instructions to deploy Epistemix to production. Total time: ~30 minutes. Total cost at launch: ~$0/month (all free tiers).

---

## Prerequisites

- GitHub account with the repository pushed
- [Supabase](https://supabase.com) account (free tier)
- [Vercel](https://vercel.com) account (free tier)
- [Fly.io](https://fly.io) account (free tier includes 3 shared-cpu machines)
- (Optional) [Stripe](https://stripe.com) account for billing
- (Optional) Anthropic API key for live Claude API calls

---

## Step 1: Supabase (Database + Auth)

### 1.1 Create Project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Name: `epistemix`
4. Database password: (save this — you'll need it)
5. Region: choose closest to your users (e.g., `eu-west-1` for Europe)

### 1.2 Run Migrations

In the Supabase SQL Editor, run each migration file in order:

1. Copy contents of `supabase/migrations/001_auth_and_profiles.sql` → Run
2. Copy contents of `supabase/migrations/002_audits.sql` → Run
3. Copy contents of `supabase/migrations/003_findings_anomalies.sql` → Run
4. Copy contents of `supabase/migrations/004_billing.sql` → Run

Alternatively, use the Supabase CLI:
```bash
supabase link --project-ref <your-project-ref>
supabase db push
```

### 1.3 Configure Auth

1. Go to Authentication → Providers
2. Enable **Email** (already enabled by default)
3. (Optional) Enable **Google OAuth**:
   - Create OAuth credentials at [console.cloud.google.com](https://console.cloud.google.com)
   - Set redirect URL: `https://<your-project>.supabase.co/auth/v1/callback`
   - Add client ID and secret in Supabase

### 1.4 Enable Realtime

1. Go to Database → Replication
2. Ensure `audits` table is in the `supabase_realtime` publication
3. (The migration already does this, but verify)

### 1.5 Note Your Keys

From Settings → API:
- **Project URL**: `https://xxxxx.supabase.co` → this is `SUPABASE_URL`
- **anon public key**: `eyJ...` → this is `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- **service_role key**: `eyJ...` → this is `SUPABASE_SERVICE_ROLE_KEY` (keep secret!)

---

## Step 2: Vercel (Web App)

### 2.1 Connect Repository

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. **Root Directory**: `web`
4. **Framework Preset**: Next.js (auto-detected)

### 2.2 Set Environment Variables

In Vercel project settings → Environment Variables:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxxxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase anon key |

### 2.3 Deploy

Click "Deploy." Vercel will:
1. Install `npm` dependencies
2. Run `next build`
3. Deploy to edge network

Your app is now live at `https://epistemix-xxxxx.vercel.app`.

### 2.4 Configure Auth Redirect

In Supabase → Authentication → URL Configuration:
- **Site URL**: `https://your-vercel-url.vercel.app`
- **Redirect URLs**: `https://your-vercel-url.vercel.app/auth/callback`

---

## Step 3: Fly.io (Worker)

### 3.1 Install Fly CLI

```bash
curl -L https://fly.io/install.sh | sh
fly auth login
```

### 3.2 Create App

```bash
fly apps create epistemix-worker --org personal
```

### 3.3 Set Secrets

```bash
fly secrets set \
  SUPABASE_URL="https://xxxxx.supabase.co" \
  SUPABASE_SERVICE_ROLE_KEY="eyJ..." \
  --app epistemix-worker

# Optional: set a default Anthropic API key for users without BYOK
fly secrets set ANTHROPIC_API_KEY="sk-ant-..." --app epistemix-worker
```

### 3.4 Deploy Worker Image

```bash
# From the repository root
fly deploy --config worker/fly.toml --remote-only
```

This builds the Docker image, pushes to Fly.io registry, and creates the base machine configuration. The actual machines are created on-demand by the Edge Function.

### 3.5 Get Fly API Token

```bash
fly tokens create deploy -x 999999h --app epistemix-worker
```

Save this token — it's needed by the Supabase Edge Function to start machines.

---

## Step 4: Supabase Edge Function

### 4.1 Deploy Edge Function

```bash
supabase functions deploy trigger-worker \
  --project-ref <your-project-ref>
```

### 4.2 Set Edge Function Secrets

```bash
supabase secrets set \
  FLY_API_TOKEN="fo1_..." \
  FLY_APP_NAME="epistemix-worker" \
  --project-ref <your-project-ref>
```

Note: `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are automatically available in Edge Functions.

### 4.3 Configure Database Webhook

1. Go to Supabase → Database → Webhooks
2. Create webhook:
   - **Name**: `trigger-worker-on-new-audit`
   - **Table**: `audits`
   - **Events**: `INSERT`
   - **Type**: Supabase Edge Function
   - **Function**: `trigger-worker`

---

## Step 5: GitHub Actions Secrets

In your GitHub repository → Settings → Secrets and variables → Actions:

| Secret | Value |
|--------|-------|
| `FLY_API_TOKEN` | Your Fly.io deploy token |

(Vercel deploys are handled by their GitHub integration automatically.)

---

## Step 6: Smoke Test

1. Open your Vercel URL
2. Sign up with email
3. Go to "New Audit"
4. Enter:
   - Topic: `Amphipolis tomb excavation`
   - Country: `Greece`
   - Discipline: `archaeology`
5. Click "Start Epistemic Audit"
6. Watch the live audit page update in real-time

If using MockConnector (no API key), you'll see limited results. With a real API key, the audit should find multiple scholars, theories, and anomalies.

---

## Environment Variable Reference

### Vercel (web)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | Supabase anonymous key |
| `STRIPE_SECRET_KEY` | No | Stripe secret key (for billing) |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | No | Stripe publishable key |

### Fly.io (worker)

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key |
| `ANTHROPIC_API_KEY` | No | Default Anthropic key (overridden by BYOK) |
| `CLAUDE_MODEL` | No | Model ID (default: `claude-sonnet-4-20250514`) |
| `MAX_BUDGET` | No | Max API budget per audit in USD (default: 10.0) |

### Supabase Edge Functions

| Variable | Required | Description |
|----------|----------|-------------|
| `FLY_API_TOKEN` | Yes | Fly.io API token for creating machines |
| `FLY_APP_NAME` | No | Fly.io app name (default: `epistemix-worker`) |
| `SUPABASE_URL` | Auto | Provided automatically |
| `SUPABASE_SERVICE_ROLE_KEY` | Auto | Provided automatically |

### Worker Runtime (set by Edge Function, not manually)

| Variable | Description |
|----------|-------------|
| `AUDIT_ID` | UUID of the audit to process |
| `AUDIT_TOPIC` | Topic string |
| `AUDIT_COUNTRY` | Country string |
| `AUDIT_DISCIPLINE` | Discipline string |
| `AUDIT_MAX_CYCLES` | Maximum cycles to run |

---

## Cost Breakdown

### Free Tier Limits

| Service | Free tier | Enough for |
|---------|-----------|-----------|
| Supabase | 500MB DB, 50K monthly active users, 500MB bandwidth | ~1000 audits |
| Vercel | 100GB bandwidth, unlimited deploys | ~10K users |
| Fly.io | 3 shared-cpu-1x machines, 256MB each | ~500 audits/month |

### Paid (when you outgrow free tiers)

| Service | Price | When to upgrade |
|---------|-------|-----------------|
| Supabase Pro | $25/month | >500MB data or need daily backups |
| Vercel Pro | $20/month | Need team features or more bandwidth |
| Fly.io | Pay-per-use | Free tier exceeded |
| Anthropic API | Per token | When using live Claude API |

### Total at launch: $0/month
### Total at ~1K users: ~$50-75/month
