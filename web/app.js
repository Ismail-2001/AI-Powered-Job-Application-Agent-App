// Character counters
const jobInput = document.getElementById('jobInput');
const charCount = document.getElementById('charCount');
const linkedinInput = document.getElementById('linkedinInput');
const linkedinCharCount = document.getElementById('linkedinCharCount');

jobInput.addEventListener('input', () => {
    charCount.textContent = jobInput.value.length;
});

linkedinInput.addEventListener('input', () => {
    linkedinCharCount.textContent = linkedinInput.value.length;
});

// Tab switching
function showTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    if (tabName === 'linkedin') {
        document.querySelector('.tab-btn:first-child').classList.add('active');
        document.getElementById('linkedinTab').classList.add('active');
    } else {
        document.querySelector('.tab-btn:last-child').classList.add('active');
        document.getElementById('jobTab').classList.add('active');
    }
}

// Load existing profile on page load
async function loadProfile() {
    try {
        const response = await fetch('http://127.0.0.1:8000/profile');
        const data = await response.json();

        if (data.success && data.profile) {
            updateProfileStatus(data.profile);
        }
    } catch (error) {
        console.log('No existing profile found or API not running');
    }
}

function updateProfileStatus(profile) {
    const statusDiv = document.getElementById('profileStatus');
    const nameEl = document.getElementById('profileName');
    const detailsEl = document.getElementById('profileDetails');
    const iconEl = statusDiv.querySelector('.status-icon');

    const name = profile.personal_info?.name || 'Unknown';
    const experienceCount = profile.experience?.length || 0;
    const skillsCount = Object.values(profile.skills || {}).flat().length;

    nameEl.textContent = name;
    detailsEl.textContent = `${experienceCount} experiences • ${skillsCount} skills`;
    iconEl.textContent = '✅';
    statusDiv.classList.add('loaded');
}

// Import LinkedIn profile
async function importLinkedIn() {
    const profileText = linkedinInput.value.trim();

    if (!profileText || profileText.length < 100) {
        alert('Please paste your full LinkedIn profile content (at least 100 characters)');
        return;
    }

    // Show progress
    document.querySelector('.linkedin-input-area').style.display = 'none';
    document.getElementById('importProgress').style.display = 'flex';

    try {
        const response = await fetch('http://127.0.0.1:8000/import-linkedin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                profile_text: profileText
            })
        });

        if (!response.ok) {
            throw new Error(`Import failed: ${response.status}`);
        }

        const data = await response.json();

        // Update profile status
        document.getElementById('profileName').textContent = data.profile.name;
        document.getElementById('profileDetails').textContent =
            `${data.profile.experience_count} experiences • ${data.profile.skills_count} skills imported`;
        document.getElementById('profileStatus').querySelector('.status-icon').textContent = '✅';
        document.getElementById('profileStatus').classList.add('loaded');

        // Hide progress, show success
        document.getElementById('importProgress').style.display = 'none';
        document.querySelector('.linkedin-input-area').style.display = 'block';

        // Clear textarea
        linkedinInput.value = '';
        linkedinCharCount.textContent = '0';

        // Show success message and switch to job tab
        alert('✅ Profile imported successfully! Now switch to "Generate CV & CL" tab to create your application.');
        showTab('job');

    } catch (error) {
        document.getElementById('importProgress').style.display = 'none';
        document.querySelector('.linkedin-input-area').style.display = 'block';
        alert(`Error: ${error.message}\n\nMake sure the API server is running on http://127.0.0.1:8000`);
    }
}

// Load profile on page load
document.addEventListener('DOMContentLoaded', loadProfile);

// Scroll to app
function scrollToApp() {
    document.getElementById('app').scrollIntoView({ behavior: 'smooth' });
}

// Process job application
async function processJob() {
    const jobDescription = jobInput.value.trim();

    if (!jobDescription || jobDescription.length < 50) {
        alert('Please enter a complete job description (at least 50 characters)');
        return;
    }

    // Hide input, show progress
    document.querySelector('.input-area').style.display = 'none';
    document.getElementById('progressArea').style.display = 'block';
    document.getElementById('resultArea').style.display = 'none';

    // Simulate progress steps
    const steps = ['step1', 'step2', 'step3', 'step4'];
    const statuses = [
        'Analyzing job requirements...',
        'Retrieving relevant experience via RAG...',
        'Customizing CV with STAR method...',
        'Generating documents...'
    ];

    let currentStep = 0;
    const progressInterval = setInterval(() => {
        if (currentStep < steps.length) {
            document.getElementById(steps[currentStep]).classList.add('active');
            document.getElementById('progressStatus').textContent = statuses[currentStep];
            document.getElementById('progressFill').style.width = `${((currentStep + 1) / steps.length) * 100}%`;
            currentStep++;
        }
    }, 1500);

    try {
        // Call the API
        const response = await fetch('http://127.0.0.1:8000/apply', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                job_description: jobDescription
            })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();

        // Stop progress animation
        clearInterval(progressInterval);

        // Mark all steps complete
        steps.forEach(step => document.getElementById(step).classList.add('active'));
        document.getElementById('progressFill').style.width = '100%';

        // Wait a moment then show results
        setTimeout(() => {
            showResults(data);
        }, 1000);

    } catch (error) {
        clearInterval(progressInterval);
        alert(`Error: ${error.message}\n\nMake sure the API server is running on http://127.0.0.1:8000`);
        resetForm();
    }
}

function showResults(data) {
    document.getElementById('progressArea').style.display = 'none';
    document.getElementById('resultArea').style.display = 'block';

    // Display job analysis
    const analysis = data.analysis;
    const roleInfo = analysis.role_info;
    const keywords = analysis.keywords;

    const analysisHTML = `
        <div style="line-height: 2;">
            <strong>Role:</strong> ${roleInfo.title}<br>
            <strong>Company:</strong> ${roleInfo.company}<br>
            <strong>Level:</strong> ${roleInfo.level}<br>
            <strong>Keywords Extracted:</strong> ${keywords.ats_keywords.length} ATS keywords
        </div>
    `;

    document.getElementById('jobAnalysis').innerHTML = analysisHTML;

    // Display generated files with download buttons
    const downloadUrls = data.download_urls;
    const files = data.files;

    const filesHTML = `
        <div style="line-height: 2;">
            <div style="margin-bottom: 20px;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <span style="font-size: 24px;">📄</span>
                    <div>
                        <strong>CV (Resume)</strong><br>
                        <small style="color: #64748b;">${files.cv}</small>
                    </div>
                </div>
                <a href="http://127.0.0.1:8000${downloadUrls.cv}" 
                   class="download-btn" 
                   download>
                    ⬇️ Download CV
                </a>
            </div>
            
            <div style="margin-bottom: 20px;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <span style="font-size: 24px;">✉️</span>
                    <div>
                        <strong>Cover Letter</strong><br>
                        <small style="color: #64748b;">${files.cover_letter}</small>
                    </div>
                </div>
                <a href="http://127.0.0.1:8000${downloadUrls.cover_letter}" 
                   class="download-btn" 
                   download>
                    ⬇️ Download Cover Letter
                </a>
            </div>
            
            <div style="margin-top: 16px; padding: 12px; background: #ecfdf5; border-radius: 8px; color: #065f46; text-align: center;">
                ✅ Your documents are ready for download!
            </div>
        </div>
    `;

    document.getElementById('generatedFiles').innerHTML = filesHTML;
}

function resetForm() {
    document.querySelector('.input-area').style.display = 'block';
    document.getElementById('progressArea').style.display = 'none';
    document.getElementById('resultArea').style.display = 'none';

    // Reset progress
    const steps = ['step1', 'step2', 'step3', 'step4'];
    steps.forEach(step => document.getElementById(step).classList.remove('active'));
    document.getElementById('progressFill').style.width = '0%';

    // Clear input
    jobInput.value = '';
    charCount.textContent = '0';
}

// Add keyboard shortcut (CMD/CTRL + Enter to submit)
jobInput.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        processJob();
    }
});
