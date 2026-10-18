"""
Comprehensive dataset of 15 authentic Brilliant Directories support articles.
Used for offline seeding, deterministic testing, and initial crawl verification.
Each article includes realistic headings, structured steps, tables, and image references.
"""

SAMPLE_ARTICLES = [
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010001",
        "title": "Configuring Membership Plans & Recurring Billing",
        "lastmod": "2026-10-01T10:00:00Z",
        "html": """
        <div class="article-content">
            <h1>Configuring Membership Plans & Recurring Billing</h1>
            <p>Brilliant Directories allows administrators to establish paid tiers, freemium options, and subscription cycles for members.</p>
            
            <h2>Prerequisites</h2>
            <p>Before enabling recurring billing, ensure your payment gateway (such as Stripe or PayPal Standard) is active in Settings &gt; Payment Gateways.</p>
            
            <h2>Step-by-Step Setup</h2>
            <ol>
                <li>From the admin sidebar, navigate to <strong>Finance &gt; Membership Plans</strong>.</li>
                <li>Locate the plan you wish to modify and click <strong>Edit</strong>.</li>
                <li>Select the <strong>Billing</strong> tab at the top of the plan editor.</li>
                <li>Set the <strong>Plan Type</strong> to <em>Paid</em>.</li>
                <li>Set <strong>Recurring Billing</strong> to <em>Enabled</em>.</li>
                <li>Specify the billing cycle: <strong>Monthly</strong>, <strong>Quarterly</strong>, or <strong>Annual</strong>.</li>
                <li>Input the <strong>Initial Setup Fee</strong> and <strong>Recurring Price</strong>.</li>
                <li>Click the green <strong>Save Changes</strong> button at the bottom right.</li>
            </ol>
            
            <h2>Billing Configuration Options</h2>
            <table>
                <thead>
                    <tr><th>Field</th><th>Description</th><th>Recommended Setting</th></tr>
                </thead>
                <tbody>
                    <tr><td>Enable Free Trial</td><td>Grants temporary access without upfront charge</td><td>Optional (14 days)</td></tr>
                    <tr><td>Auto-Suspend Delinquent</td><td>Suspends profile when subscription fails 3 times</td><td>Enabled</td></tr>
                    <tr><td>Prorate Upgrades</td><td>Calculates unused days when switching tiers</td><td>Enabled</td></tr>
                </tbody>
            </table>
            
            <p>The billing dashboard displays invoice history for all active recurring subscriptions.</p>
            <img src="https://support.brilliantdirectories.com/images/billing-tab-setup.png" alt="Membership Billing Tab Settings" />
            <p>Screenshot showing the Billing tab with recurring options toggled on.</p>
        </div>
        """
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010002",
        "title": "Setting Up Automated Lead Matching & Distribution",
        "lastmod": "2026-10-02T11:00:00Z",
        "html": """
        <div class="article-content">
            <h1>Setting Up Automated Lead Matching & Distribution</h1>
            <p>The Lead System matches customer inquiries directly with relevant directory members based on geographical radius and category taxonomy.</p>
            
            <h2>Enabling Automatic Matching</h2>
            <ol>
                <li>Go to <strong>Leads &gt; Lead Settings</strong> in your admin dashboard.</li>
                <li>Under <strong>Matching Rules</strong>, choose between <em>Auto-Match and Notify</em> or <em>Admin Moderation Required</em>.</li>
                <li>Define the <strong>Matching Radius</strong> (default is 25 miles / 40 km).</li>
                <li>Select the maximum number of members who can receive a single lead (recommended: 3 to 5).</li>
                <li>Click <strong>Save Lead Settings</strong>.</li>
            </ol>
            
            <h2>Lead Notification Preferences</h2>
            <p>Members receive email alerts containing the inquiry overview. Contact details are masked until the member accepts the lead.</p>
            <img src="https://support.brilliantdirectories.com/images/lead-matching-panel.png" alt="Lead Matching Rules Configuration" />
            <p>The screenshot shows radius sliders and category toggle checkboxes.</p>
        </div>
        """
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010003",
        "title": "Connecting Custom Domains & SSL Certificates",
        "lastmod": "2026-10-03T09:30:00Z",
        "html": """
        <div class="article-content">
            <h1>Connecting Custom Domains & SSL Certificates</h1>
            <p>Launch your directory under your own primary branded domain name.</p>
            
            <h2>DNS Configuration</h2>
            <p>Create the following DNS records at your domain registrar (GoDaddy, Namecheap, Cloudflare):</p>
            <ul>
                <li><strong>A Record:</strong> Host <code>@</code> points to IP <code>54.208.182.193</code></li>
                <li><strong>CNAME Record:</strong> Host <code>www</code> points to <code>directoryup.com</code></li>
            </ul>
            
            <h2>Domain Verification & Free SSL</h2>
            <ol>
                <li>In Brilliant Directories, go to <strong>Settings &gt; Domain Manager</strong>.</li>
                <li>Type your domain name without <code>https://</code> (e.g. <code>mycustomdirectory.com</code>).</li>
                <li>Click <strong>Verify DNS Records</strong>.</li>
                <li>Once DNS propagates (usually 15–60 minutes), click <strong>Install Free Let's Encrypt SSL</strong>.</li>
            </ol>
        </div>
        """
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010004",
        "title": "Integrating Google Maps API for Location Searches",
        "lastmod": "2026-10-04T14:15:00Z",
        "html": """
        <div class="article-content">
            <h1>Integrating Google Maps API for Location Searches</h1>
            <p>Enable precise geolocation filtering, address autocomplete, and radius search on directory maps.</p>
            
            <h2>Required Google Cloud APIs</h2>
            <p>Enable these three APIs in your Google Cloud Console:</p>
            <ul>
                <li>Maps JavaScript API</li>
                <li>Geocoding API</li>
                <li>Places API</li>
            </ul>
            
            <h2>Entering the API Key</h2>
            <ol>
                <li>In the admin dashboard, go to <strong>Settings &gt; General Settings</strong>.</li>
                <li>Click on the <strong>Integrations</strong> tab.</li>
                <li>Paste your API key into the <strong>Google Maps JavaScript API Key</strong> field.</li>
                <li>Click <strong>Save Changes</strong>.</li>
            </ol>
            <img src="https://support.brilliantdirectories.com/images/google-maps-integration.png" alt="Google Maps Key Field in Settings" />
            <p>Verify that the Maps status indicator turns green after saving.</p>
        </div>
        """
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010005",
        "title": "Managing Member Categories & Sub-Categories",
        "lastmod": "2026-10-05T12:00:00Z",
        "html": """
        <div class="article-content">
            <h1>Managing Member Categories & Sub-Categories</h1>
            <p>Structure your directory taxonomy with 3 levels of depth: Top Categories, Sub-Categories, and Sub-Sub-Categories.</p>
            
            <h2>Adding a Top Category</h2>
            <ol>
                <li>Navigate to <strong>Members &gt; Member Categories</strong>.</li>
                <li>Click <strong>Add Top Category</strong>.</li>
                <li>Input the category name, clean URL slug, and icon class.</li>
                <li>Click <strong>Save Category</strong>.</li>
            </ol>
            
            <h2>Bulk Importing Categories</h2>
            <p>You can upload a CSV file with columns: <code>Top Level</code>, <code>Sub Level</code>, and <code>Sub-Sub Level</code>. The platform automatically associates them in hierarchy.</p>
        </div>
        """
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010006",
        "title": "Configuring Stripe & PayPal Payment Gateways",
        "lastmod": "2026-10-06T15:20:00Z",
        "html": """
        <div class="article-content">
            <h1>Configuring Stripe & PayPal Payment Gateways</h1>
            <p>Accept credit cards, debit cards, and recurring subscriptions directly on your directory site.</p>
            
            <h2>Connecting Stripe (Recommended)</h2>
            <ol>
                <li>Navigate to <strong>Settings &gt; Payment Gateways</strong>.</li>
                <li>Select <strong>Stripe</strong> from the dropdown list.</li>
                <li>Enter your <strong>Stripe Publishable Key</strong> and <strong>Stripe Secret Key</strong>.</li>
                <li>Configure the Stripe Webhook URL shown on the screen inside your Stripe Dashboard for <code>invoice.payment_succeeded</code> and <code>customer.subscription.deleted</code> events.</li>
                <li>Click <strong>Save & Test Connection</strong>.</li>
            </ol>
            
            <h2>Currency Settings</h2>
            <p>Set default billing currency under <strong>General Settings &gt; Localization</strong>. All membership tiers will bill in this currency.</p>
        </div>
        """
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010007",
        "title": "Setting Up Webhooks & Zapier Integration",
        "lastmod": "2026-10-07T08:45:00Z",
        "html": """
        <div class="article-content">
            <h1>Setting Up Webhooks & Zapier Integration</h1>
            <p>Connect Brilliant Directories to external CRMs (HubSpot, Salesforce, ActiveCampaign) using native webhooks or Zapier.</p>
            
            <h2>Available Webhook Triggers</h2>
            <ul>
                <li><code>member_signup</code> — fires when a user completes registration</li>
                <li><code>lead_generated</code> — fires when a visitor submits a contact/lead form</li>
                <li><code>review_submitted</code> — fires when a member review is posted</li>
                <li><code>subscription_cancelled</code> — fires on membership cancellation</li>
            </ul>
            
            <h2>Configuring Outbound Webhooks</h2>
            <ol>
                <li>Go to <strong>Developer Hub &gt; Webhooks</strong>.</li>
                <li>Click <strong>Create Webhook</strong>.</li>
                <li>Select the trigger event and paste your destination endpoint URL.</li>
                <li>Optionally provide an authorization header secret.</li>
                <li>Test the payload and click <strong>Activate Webhook</strong>.</li>
            </ol>
        </div>
        """
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010008",
        "title": "Creating Discount Promo Codes & Coupons",
        "lastmod": "2026-10-08T16:10:00Z",
        "html": """
        <div class="article-content">
            <h1>Creating Discount Promo Codes & Coupons</h1>
            <p>Offer percentage or fixed-amount discounts during membership registration or upgrades.</p>
            
            <h2>Coupon Creation Steps</h2>
            <ol>
                <li>Navigate to <strong>Finance &gt; Promo Codes</strong>.</li>
                <li>Click <strong>New Promo Code</strong>.</li>
                <li>Enter the coupon code name (e.g., <code>SUMMER50</code>).</li>
                <li>Select discount type: <strong>Percentage (%)</strong> or <strong>Fixed Amount ($)</strong>.</li>
                <li>Choose applicable membership plans or apply to all plans.</li>
                <li>Set an optional expiration date and maximum usage count.</li>
                <li>Click <strong>Save Promo Code</strong>.</li>
            </ol>
        </div>
        """
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010009",
        "title": "Customizing Automated Email Notifications & Templates",
        "lastmod": "2026-10-09T13:30:00Z",
        "html": """
        <div class="article-content">
            <h1>Customizing Automated Email Notifications & Templates</h1>
            <p>Modify welcome emails, lead notifications, billing invoices, and password reset messages.</p>
            
            <h2>Editing Email Templates</h2>
            <ol>
                <li>Go to <strong>Emails &gt; Email Templates</strong>.</li>
                <li>Locate the template (e.g. <code>welcome-member</code> or <code>lead-matched</code>).</li>
                <li>Click <strong>Edit Template</strong>.</li>
                <li>Use variable placeholders such as <code>%%%first_name%%%</code>, <code>%%%listing_title%%%</code>, and <code>%%%login_url%%%</code>.</li>
                <li>Preview and click <strong>Save Changes</strong>.</li>
            </ol>
        </div>
        """
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010010",
        "title": "Enabling Google reCAPTCHA v2 / v3 for Spam Protection",
        "lastmod": "2026-10-10T10:00:00Z",
        "html": """
        <div class="article-content">
            <h1>Enabling Google reCAPTCHA v2 / v3 for Spam Protection</h1>
            <p>Protect registration forms, contact inquiries, and review submissions from automated bot spam.</p>
            
            <h2>Configuration Steps</h2>
            <ol>
                <li>Generate Site Key and Secret Key at <code>google.com/recaptcha</code> (choose reCAPTCHA v2 Invisible or Checkbox).</li>
                <li>In your Brilliant Directories dashboard, open <strong>Settings &gt; General Settings &gt; Integrations</strong>.</li>
                <li>Paste your keys in <strong>Google reCAPTCHA Site Key</strong> and <strong>Secret Key</strong>.</li>
                <li>Toggle <strong>Enable on Member Sign-up</strong> and <strong>Enable on Lead Forms</strong> to <em>Yes</em>.</li>
                <li>Click <strong>Save Settings</strong>.</li>
            </ol>
        </div>
        """
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010011",
        "title": "Customizing Search Filters & Member Search Results",
        "lastmod": "2026-10-11T14:40:00Z",
        "html": """
        <div class="article-content">
            <h1>Customizing Search Filters & Member Search Results</h1>
            <p>Tailor search sidebars and result cards with custom member fields, badges, and sorting criteria.</p>
            
            <h2>Modifying Search Fields</h2>
            <ol>
                <li>Go to <strong>Content &gt; Edit Post Types</strong>.</li>
                <li>Edit <strong>Member Listings</strong>.</li>
                <li>Under the <strong>Search Results View</strong> tab, choose grid or list layout.</li>
                <li>Under <strong>Sidebar Search Module</strong>, toggle which filters appear: Keyword, Category, Location, Distance Radius, Rating.</li>
                <li>Save post type configurations.</li>
            </ol>
        </div>
        """
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010012",
        "title": "Importing Members via CSV & Mapping Custom Fields",
        "lastmod": "2026-10-12T11:15:00Z",
        "html": """
        <div class="article-content">
            <h1>Importing Members via CSV & Mapping Custom Fields</h1>
            <p>Batch import existing member directories, business profiles, and contact lists.</p>
            
            <h2>File Preparation Guidelines</h2>
            <ul>
                <li>CSV file encoded in UTF-8 format.</li>
                <li>Mandatory columns: <code>email</code>, <code>first_name</code>, <code>last_name</code>, <code>plan_id</code>.</li>
                <li>Optional columns: <code>company</code>, <code>phone_number</code>, <code>address1</code>, <code>city</code>, <code>state_code</code>, <code>zip_code</code>.</li>
            </ul>
            
            <h2>Import Procedure</h2>
            <ol>
                <li>Navigate to <strong>Members &gt; Import Members</strong>.</li>
                <li>Upload your CSV file.</li>
                <li>Map CSV column headers to Brilliant Directories profile database fields.</li>
                <li>Choose whether to send automatic welcome login emails.</li>
                <li>Click <strong>Start Import</strong>.</li>
            </ol>
        </div>
        """
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010013",
        "title": "Configuring SEO Meta Tags, 301 Redirects & Robots.txt",
        "lastmod": "2026-10-13T09:00:00Z",
        "html": """
        <div class="article-content">
            <h1>Configuring SEO Meta Tags, 301 Redirects & Robots.txt</h1>
            <p>Optimize organic search indexing and manage canonical URL redirects.</p>
            
            <h2>Global SEO Templates</h2>
            <ol>
                <li>Navigate to <strong>Settings &gt; SEO Templates</strong>.</li>
                <li>Edit default dynamic meta tags for category pages, city directories, and member profiles.</li>
                <li>Use variable tags: <code>%%%profession%%% in %%%city%%%, %%%state%%%</code>.</li>
            </ol>
            
            <h2>Setting Up 301 Redirects</h2>
            <ol>
                <li>Go to <strong>Developer Hub &gt; 301 Redirects</strong>.</li>
                <li>Click <strong>Add 301 Redirect</strong>.</li>
                <li>Enter the legacy URL path and target destination URL.</li>
                <li>Save redirect.</li>
            </ol>
        </div>
        """
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010014",
        "title": "Setting Up Sub-Accounts & Multi-Listing Memberships",
        "lastmod": "2026-10-14T17:00:00Z",
        "html": """
        <div class="article-content">
            <h1>Setting Up Sub-Accounts & Multi-Listing Memberships</h1>
            <p>Allow parent businesses or agency members to manage multiple branch locations or staff profiles under a single master login.</p>
            
            <h2>Enabling Sub-Accounts on a Membership Plan</h2>
            <ol>
                <li>Navigate to <strong>Finance &gt; Membership Plans</strong>.</li>
                <li>Edit the target plan and select the <strong>Sub-Accounts</strong> tab.</li>
                <li>Set <strong>Sub-Accounts Status</strong> to <em>Active</em>.</li>
                <li>Define the <strong>Max Sub-Accounts Allowed</strong> (e.g. 5 or Unlimited).</li>
                <li>Choose whether sub-accounts share the parent billing or require separate checkout.</li>
                <li>Click <strong>Save Changes</strong>.</li>
            </ol>
        </div>
        """
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010015",
        "title": "Managing Community Reviews & Moderation Settings",
        "lastmod": "2026-10-15T10:30:00Z",
        "html": """
        <div class="article-content">
            <h1>Managing Community Reviews & Moderation Settings</h1>
            <p>Control visitor star ratings, member responses, and review publication workflows.</p>
            
            <h2>Review Moderation Rules</h2>
            <ol>
                <li>Go to <strong>Members &gt; Member Reviews</strong>.</li>
                <li>Click <strong>Review Settings</strong>.</li>
                <li>Choose default moderation status: <em>Auto-Approve</em> or <em>Admin Must Approve</em>.</li>
                <li>Enable email notification to member when a new review is posted.</li>
                <li>Toggle whether members can reply publicly to reviews.</li>
                <li>Click <strong>Save Settings</strong>.</li>
            </ol>
        </div>
        """
    }
]
