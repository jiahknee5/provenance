# Public Data Sources for Candidate Matching

Last checked: 2026-06-17

Scope: data that Provenance could collect from public or user-authorized services to enrich Gauntlet candidate profiles and match people to program requirements. This is product research, not legal advice. For anything that affects admission, hiring, scholarships, employment, or other eligibility decisions, review with counsel before launch.

## Executive Recommendation

Use a consent-first hybrid:

- Tom export seeds the profile with first-party Gauntlet fields.
- Participant self-intake confirms identity, goals, role, constraints, and links.
- Official APIs fetch public evidence only when the participant provides or confirms a handle/URL.
- Store evidence as claims with citations, not as an opaque background dossier.

Best initial sources:

1. GitHub and GitLab for software-building evidence.
2. YouTube for public creator/teaching signals if the person supplies a channel.
3. Personal websites, blogs, portfolios, resumes, and package registries when supplied by the participant.
4. LinkedIn as self-attested/OIDC identity and a user-provided URL, not as open enrichment.

Avoid for candidate matching:

- Facebook and Instagram candidate enrichment. Access is narrow, app-review-heavy, and Meta policy risk is high.
- Scraping logged-out or logged-in social pages.
- Inferring sensitive traits, protected-class proxies, health, family status, financial stress, politics, religion, or similar fields.
- Fully automated accept/reject decisions based on third-party social data.

## Platform Matrix

| Source | What we can reliably obtain | Access model | Useful for matching | Main limits / risks |
| --- | --- | --- | --- | --- |
| GitHub | Public profile fields, public repos, repo topics, public events, contributor stats, followers/following counts, public email if the user made it public and the API request is authenticated. | Public REST API works unauthenticated for public resources, with much better limits when authenticated. | Strong technical evidence: languages, project recency, OSS collaboration, repo topics, issue/PR activity, writing in READMEs. | Public events are not real-time and can lag. Private repos and private emails require user auth and permissions. Do not treat activity volume as skill by itself. |
| GitLab | Public user search/profile fields, public project metadata, project topics/stars/forks/activity, contribution events with authenticated access. | OAuth/PAT recommended; public project endpoint can be unauthenticated when the project is public. | Similar to GitHub, especially for self-hosted/devops candidates. | User event endpoints require `read_user` or `api`. Private email and admin fields are not available to us. GitLab rate limits vary by GitLab.com versus self-managed instance. |
| LinkedIn | Authenticated user's OIDC lite profile: subject ID, name, given/family name, picture, locale, optional email. | Sign in with LinkedIn using OpenID Connect. Most other permissions or talent APIs require LinkedIn approval/partner access. | Identity confirmation and participant-provided profile URL/headline. | Not a public enrichment source. Talent/recruiting access is gated. Do not scrape or try to retrieve other members' profiles. |
| X | Public user metadata, bio, location string, URL, created date, public metrics, protected flag, public posts and post public metrics, depending on endpoint/tier. | X API v2 with bearer/user tokens and tiered limits. | Optional signal for public technical/community presence when user supplies handle. | No third-party email. High noise, paid/tiered access, protected accounts, and public discourse can reveal sensitive/protected traits. Low priority for MVP. |
| YouTube | Channel snippet/statistics/contentDetails/topicDetails by channel ID/handle; video snippets/statistics; public comment threads by channel/video. | YouTube Data API key/OAuth depending on endpoint. Many read endpoints cost 1 quota unit. | Teaching, demo, community-building, technical communication, consistency of public content. | Search quotas are constrained; comments can be noisy and may include others' personal data. Avoid sentiment/personality scoring. |
| Facebook | Authenticated user's basic public profile fields through Facebook Login (`id`, name fields, picture, short name); email only with permission if available. | User access token and permissions. | Login/identity only, if needed. | Poor fit for candidate enrichment. Third-party profile access is not generally available. Meta policy and app review make this high-risk. |
| Instagram | Business Discovery can provide basic metadata/metrics about other Instagram professional accounts. Instagram APIs focus on businesses/creators managing their own presence. | Instagram professional account, Facebook/Instagram login, permissions, app review. | Usually not relevant unless a candidate is explicitly applying as a creator/community builder and supplies a professional account. | Not a general personal-profile enrichment source. Instagram Basic Display API has been deprecated. Avoid for MVP. |
| Personal site / blog / portfolio | Public pages, projects, resume, case studies, writing, contact links. | User-provided URL; fetch with normal HTTP and respect robots/terms. | High-signal evidence when cited: artifacts, technical writing, project depth. | Requires identity resolution and freshness checks. Do not collect hidden or non-public pages. |
| Package registries / technical communities | Public packages, maintainership, project metadata, docs, releases, public profile pages. | Public APIs/pages, ideally user-supplied handles. | Evidence of shipping/maintaining software. | Needs source-specific policy checks before production. Treat as phase 2. |

## Data Contract Shape

Every imported signal should become an evidence-backed claim:

```json
{
  "claim_id": "uuid",
  "candidate_id": "uuid",
  "source": "github",
  "source_subject": "octocat",
  "claim_type": "public_project",
  "claim_text": "Candidate maintains a public repository about evals.",
  "evidence_url": "https://github.com/example/evals",
  "evidence_excerpt": "README/project metadata excerpt",
  "observed_at": "2026-06-17T00:00:00Z",
  "collection_method": "official_api",
  "consent_basis": "participant_supplied_handle",
  "confidence": "high",
  "decision_use": "assistive_only"
}
```

Keep raw third-party data minimal. Prefer normalized claims plus source URLs, timestamps, and the original field values needed to re-check the claim.

## Intake Implications

Ask participants to provide:

- GitHub username.
- GitLab username or instance URL.
- LinkedIn profile URL and optionally Sign in with LinkedIn for identity.
- Personal website, portfolio, resume, blog, package registry handles.
- YouTube channel only if relevant to their application.
- Explicit consent checkbox for fetching public data from submitted handles.

Do not ask for Facebook, Instagram, or X as required fields. If included, make them optional free-form links and do not use them for eligibility ranking in the MVP.

## Matching Use Policy

Use collected data to:

- Personalize the cohort website.
- Surface candidate strengths with citations.
- Suggest program tracks or mentor matches.
- Let humans inspect the evidence behind a recommendation.

Do not use collected data to:

- Auto-accept, auto-reject, or down-rank people without human review.
- Infer protected or sensitive traits.
- Score personality, mental health, family status, political/religious views, disability, age, race, sex, national origin, or similar attributes.
- Produce unreviewed background reports for employment-style decisions.

## Compliance Notes

Social and public-web screening can cross into regulated background-check territory if reports are used for employment or similar eligibility decisions. FTC guidance says employment background checks can include social media, but FCRA duties still apply to companies providing or using such reports. CFPB guidance similarly treats background dossiers and algorithmic scores for employment decisions as potentially covered by FCRA. EEOC/FTC/CFPB/DOJ have also stated that automated systems do not get an exemption from civil-rights and consumer-protection laws.

For Provenance, that means:

- Keep the first release assistive and transparent.
- Provide candidate access/correction flows for imported claims.
- Maintain claim-level provenance and freshness.
- Audit for disparate impact before using any score in a real selection workflow.
- Escalate to legal review before any employment, admission, funding, or other eligibility decisioning.

## Official Sources Checked

- GitHub users API: https://docs.github.com/en/rest/users/users
- GitHub repos API: https://docs.github.com/en/rest/repos/repos
- GitHub events API: https://docs.github.com/en/rest/activity/events
- GitHub rate limits: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- GitLab users API: https://docs.gitlab.com/api/users/
- GitLab events API: https://docs.gitlab.com/api/events/
- GitLab projects API: https://docs.gitlab.com/api/projects/
- GitLab REST authentication: https://docs.gitlab.com/api/rest/authentication/
- GitLab rate limits: https://docs.gitlab.com/security/rate_limits/
- LinkedIn OIDC sign-in: https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin-v2
- LinkedIn API access overview: https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access
- X API data dictionary: https://docs.x.com/x-api/fundamentals/data-dictionary
- X API rate limits: https://docs.x.com/x-api/fundamentals/rate-limits
- YouTube channels.list: https://developers.google.com/youtube/v3/docs/channels/list
- YouTube videos.list: https://developers.google.com/youtube/v3/docs/videos/list
- YouTube commentThreads.list: https://developers.google.com/youtube/v3/docs/commentThreads/list
- YouTube quota costs: https://developers.google.com/youtube/v3/determine_quota_cost
- Facebook Graph API User reference: https://developers.facebook.com/docs/graph-api/reference/user/
- Instagram Business Discovery: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/business-discovery/
- Instagram Platform changelog: https://developers.facebook.com/docs/instagram-platform/changelog/
- Meta Developer Policies: https://developers.facebook.com/devpolicy/
- FTC on FCRA and social media: https://www.ftc.gov/business-guidance/blog/2011/06/fair-credit-reporting-act-social-media-what-businesses-should-know
- FTC on employment background screeners and FCRA: https://www.ftc.gov/business-guidance/resources/what-employment-background-screening-companies-need-know-about-fair-credit-reporting-act
- CFPB Circular 2024-06 on background dossiers and algorithmic scores: https://www.consumerfinance.gov/compliance/circulars/consumer-financial-protection-circular-2024-06-background-dossiers-and-algorithmic-scores-for-hiring-promotion-and-other-employment-decisions/
- EEOC/DOJ/FTC/CFPB AI joint statement: https://www.eeoc.gov/newsroom/eeoc-chair-burrows-joins-doj-cfpb-and-ftc-officials-release-joint-statement-artificial
