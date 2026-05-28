let allJobs = [];

document.addEventListener('DOMContentLoaded', () => {
    loadJobs();
    
    // Setup filter buttons
    document.querySelectorAll('.btn-toggle').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.btn-toggle').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            renderJobs();
        });
    });

    // Setup search
    document.getElementById('search-input').addEventListener('input', renderJobs);
    
    // Close modal on overlay click or close button
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-overlay') || e.target.closest('.modal-close')) {
            closeModal();
        }
    });
    
    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });
});

async function loadJobs() {
    const grid = document.getElementById('jobs-grid');
    grid.innerHTML = `
        <div class="loading-state">
            <div class="spinner"></div>
            <p>Loading your opportunities...</p>
        </div>
    `;

    try {
        const response = await fetch('/api/jobs');
        const data = await response.json();
        allJobs = data.jobs || [];
        updateStats();
        renderJobs();
    } catch (error) {
        console.error('Error fetching jobs:', error);
        grid.innerHTML = `<div class="loading-state"><p style="color:var(--danger)">Error loading jobs. Ensure the backend is running.</p></div>`;
    }
}

function updateStats() {
    document.getElementById('total-jobs').textContent = allJobs.length;
    document.getElementById('applied-jobs').textContent = allJobs.filter(j => j.status === 'APPLIED').length;
}

function renderJobs() {
    const grid = document.getElementById('jobs-grid');
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const filterType = document.querySelector('.btn-toggle.active').dataset.filter;

    let filtered = allJobs.filter(job => {
        // Apply Search
        const searchString = `${job.required_skills} ${job.match_reason} ${job.author_profile}`.toLowerCase();
        if (searchTerm && !searchString.includes(searchTerm)) return false;

        // Apply Toggle Filter
        if (filterType === 'matches' && job.match_score < 80) return false;
        if (filterType === 'applied' && job.status !== 'APPLIED') return false;
        
        return true;
    });

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="loading-state">
                <i class="fa-solid fa-ghost" style="font-size: 2rem; margin-bottom:1rem; opacity:0.5"></i>
                <p>No jobs found matching your filters.</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = filtered.map(job => createJobCard(job)).join('');
}

function createJobCard(job) {
    let scoreClass = 'score-low';
    if (job.match_score >= 80) scoreClass = 'score-high';
    else if (job.match_score >= 50) scoreClass = 'score-med';

    const dateStr = new Date(job.scraped_at).toLocaleString();
    
    // Parse skills nicely
    const skills = job.required_skills ? job.required_skills.split(',').map(s => s.trim()).filter(s => s) : [];
    const skillsHtml = skills.slice(0, 5).map(s => `<span class="skill-tag">${s}</span>`).join('');
    const extraSkills = skills.length > 5 ? `<span class="skill-tag">+${skills.length - 5}</span>` : '';

    const isRemote = job.is_remote_or_sponsored ? '<i class="fa-solid fa-globe" style="color:var(--success)" title="Remote/Sponsored"></i>' : '<i class="fa-solid fa-building" style="color:var(--warning)" title="On-site"></i>';

    const postLink = job.post_url ? `<a href="${job.post_url}" target="_blank" class="btn-icon" onclick="event.stopPropagation()"><i class="fa-solid fa-arrow-up-right-from-square"></i> Post</a>` : `<a class="btn-icon disabled"><i class="fa-solid fa-link-slash"></i> No Link</a>`;
    const authorLink = job.author_profile ? `<a href="${job.author_profile}" target="_blank" class="btn-icon" onclick="event.stopPropagation()"><i class="fa-solid fa-user"></i> Author</a>` : `<a class="btn-icon disabled"><i class="fa-solid fa-user-slash"></i> Unknown</a>`;

    return `
        <div class="job-card" onclick="openJobDetail(${job.id})" style="cursor:pointer">
            <div class="card-header">
                <div class="card-meta">
                    <span class="status-badge status-${job.status}">${job.status}</span>
                    <span class="date-badge"><i class="fa-regular fa-clock"></i> ${dateStr}</span>
                </div>
                <div class="score-badge ${scoreClass}">${job.match_score}</div>
            </div>
            
            <p class="job-reason">${job.match_reason}</p>
            
            <div style="display:flex; align-items:center; gap:0.5rem; font-size:0.875rem; color:var(--text-secondary)">
                ${isRemote} 
                <span>Emails: ${job.emails || 'None'}</span>
            </div>

            <div class="skills-container">
                ${skillsHtml}
                ${extraSkills}
            </div>

            <div class="card-actions">
                ${postLink}
                ${authorLink}
            </div>
        </div>
    `;
}

async function openJobDetail(jobId) {
    // Show a quick loading state or use cached data while fetching
    let job = allJobs.find(j => j.id === jobId);
    if (!job) return;
    
    // Fetch full details
    try {
        const response = await fetch(`/api/jobs/${jobId}`);
        const data = await response.json();
        if (data.job) {
            job = data.job;
        }
    } catch (e) {
        console.error("Failed to fetch full job details", e);
    }
    
    // Extract recruiter name from profile URL
    let recruiterName = 'Unknown';
    if (job.author_profile) {
        const match = job.author_profile.match(/\/in\/([^\/]+)/);
        if (match) {
            recruiterName = match[1].replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        }
    }
    
    let scoreClass = 'score-low';
    if (job.match_score >= 80) scoreClass = 'score-high';
    else if (job.match_score >= 50) scoreClass = 'score-med';
    
    const dateStr = new Date(job.scraped_at).toLocaleString();
    const skills = job.required_skills ? job.required_skills.split(',').map(s => s.trim()).filter(s => s) : [];
    const skillsHtml = skills.map(s => `<span class="skill-tag">${s}</span>`).join('');
    
    const postLink = job.post_url ? `<a href="${job.post_url}" target="_blank" class="btn-icon"><i class="fa-solid fa-arrow-up-right-from-square"></i> Open Post</a>` : '';
    const authorLink = job.author_profile ? `<a href="${job.author_profile}" target="_blank" class="btn-icon"><i class="fa-solid fa-user"></i> View Profile</a>` : '';
    
    // Truncate text for display
    const postText = job.text || 'No post text available.';
    
    // Build email section
    const emailSection = job.email_body ? `
        <div class="detail-section">
            <h3><i class="fa-solid fa-envelope"></i> Generated Email</h3>
            <div class="detail-email-content">${job.email_body}</div>
        </div>
    ` : '';
    
    // Build connection invite section
    const inviteSection = job.connection_invite ? `
        <div class="detail-section">
            <h3><i class="fa-solid fa-user-plus"></i> Connection Invite</h3>
            <div class="detail-email-content" style="background: rgba(139, 92, 246, 0.06); border-color: rgba(139, 92, 246, 0.15);">${job.connection_invite.replace(/\n/g, '<br>')}</div>
        </div>
    ` : '';
    
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-container">
            <button class="modal-close"><i class="fa-solid fa-xmark"></i></button>
            
            <div class="modal-header">
                <div class="modal-title-row">
                    <div class="score-badge ${scoreClass}" style="width:55px;height:55px;font-size:1.2rem">${job.match_score}</div>
                    <div>
                        <h2 class="modal-recruiter-name">${recruiterName}</h2>
                        <span class="date-badge"><i class="fa-regular fa-clock"></i> ${dateStr}</span>
                    </div>
                    <span class="status-badge status-${job.status}" style="margin-left:auto">${job.status}</span>
                </div>
            </div>
            
            <div class="modal-body">
                <div class="detail-section">
                    <h3><i class="fa-solid fa-bullseye"></i> Match Reason</h3>
                    <p>${job.match_reason || 'N/A'}</p>
                </div>
                
                <div class="detail-section">
                    <h3><i class="fa-solid fa-code"></i> Required Skills</h3>
                    <div class="skills-container">${skillsHtml || '<span class="text-secondary">None listed</span>'}</div>
                </div>
                
                ${inviteSection}
                ${emailSection}
                
                <div class="detail-section">
                    <h3><i class="fa-brands fa-linkedin"></i> Original Post</h3>
                    <div class="detail-post-text">${postText}</div>
                </div>
            </div>
            
            <div class="modal-footer">
                ${postLink}
                ${authorLink}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    // Trigger animation
    requestAnimationFrame(() => {
        modal.classList.add('modal-visible');
    });
}

function closeModal() {
    const modal = document.querySelector('.modal-overlay');
    if (!modal) return;
    modal.classList.remove('modal-visible');
    modal.addEventListener('transitionend', () => modal.remove(), { once: true });
}
