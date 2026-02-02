// Character counter
const jobInput = document.getElementById('jobInput');
const charCount = document.getElementById('charCount');

jobInput.addEventListener('input', () => {
    charCount.textContent = jobInput.value.length;
});

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
    
    // Display generated files
    const files = data.files;
    const filesHTML = `
        <div style="line-height: 2;">
            <div style="margin-bottom: 12px;">
                <strong>📄 CV:</strong><br>
                <code style="background: #f1f5f9; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                    ${files.cv}
                </code>
            </div>
            <div>
                <strong>✉️ Cover Letter:</strong><br>
                <code style="background: #f1f5f9; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                    ${files.cover_letter}
                </code>
            </div>
            <div style="margin-top: 16px; padding: 12px; background: #ecfdf5; border-radius: 8px; color: #065f46;">
                ✅ Files saved to your output folder
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
