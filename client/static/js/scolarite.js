/**
 * scolarite.js — Portail Scolarité Client UI Logic
 */

'use strict';

const $ = (id) => document.getElementById(id);

// Config globale de session
let currentUser = null;

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', async () => {
    await checkSession();
    setupEventListeners();
    setupMobileMenu();
});

// Vérifier si une session est déjà ouverte
async function checkSession() {
    try {
        const resp = await fetch('/api/scolarite/status');
        const data = await resp.json();
        
        if (data.authenticated) {
            currentUser = data;
            showDashboard();
        } else {
            showLogin();
        }
    } catch (e) {
        console.error("Erreur de session scolarité:", e);
        showLogin();
    }
}

// Configurer les écouteurs d'événements
function setupEventListeners() {
    // Connexion
    $('btn-login-scolarite').addEventListener('click', login);
    $('scolarite-password').addEventListener('keyup', (e) => {
        if (e.key === 'Enter') login();
    });

    // Déconnexion
    $('btn-logout-scolarite').addEventListener('click', logout);

    // Onglets (Tabs) avec animations fluides
    document.querySelectorAll('.scolarite-tabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            // Changer l'état actif des boutons d'onglet
            document.querySelectorAll('.scolarite-tabs .tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Fermer le menu mobile s'il est ouvert
            closeMobileMenu();

            switchTab(tabId);
        });
    });

    // Saisie des notes (Enseignant)
    $('form-add-grade').addEventListener('submit', addGrade);

    // Envoi de message (Étudiant / Enseignant)
    $('form-send-admin-message').addEventListener('submit', sendAdminMessage);
}

// Gestion des transitions d'onglets animées
function switchTab(tabId) {
    const contents = document.querySelectorAll('.scolarite-content .tab-content');
    
    // 1. Cacher tous les onglets en retirant la classe 'show' (déclenche la transition de fondu)
    contents.forEach(c => {
        c.classList.remove('show');
    });

    // Attendre la fin de la transition d'opacité avant de changer le display
    setTimeout(() => {
        contents.forEach(c => {
            c.classList.remove('active');
        });

        // 2. Activer l'onglet cible (display block)
        const target = $(tabId);
        target.classList.add('active');

        // 3. Forcer un reflow pour s'assurer que le navigateur applique le display block
        target.offsetHeight;

        // 4. Ajouter la classe 'show' (déclenche l'opacité et la translation)
        target.classList.add('show');
    }, 150);
}

// Gestion du menu tiroir (Mobile Drawer)
function setupMobileMenu() {
    const menuToggle = $('menu-toggle');
    const menuClose = $('menu-close');
    const backdrop = $('sidebar-backdrop');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', openMobileMenu);
    }
    if (menuClose) {
        menuClose.addEventListener('click', closeMobileMenu);
    }
    if (backdrop) {
        backdrop.addEventListener('click', closeMobileMenu);
    }
}

function openMobileMenu() {
    const tabs = $('scolarite-tabs');
    const backdrop = $('sidebar-backdrop');
    
    tabs.classList.add('open');
    backdrop.classList.remove('hidden');
    // Force reflow
    backdrop.offsetHeight;
    backdrop.classList.add('show');
}

function closeMobileMenu() {
    const tabs = $('scolarite-tabs');
    const backdrop = $('sidebar-backdrop');
    
    tabs.classList.remove('open');
    backdrop.classList.remove('show');
    setTimeout(() => {
        if (!tabs.classList.contains('open')) {
            backdrop.classList.add('hidden');
        }
    }, 300);
}

// Connexion
async function login() {
    const username = $('scolarite-username').value.trim();
    const password = $('scolarite-password').value.trim();
    const loginBtn = $('btn-login-scolarite');

    if (!username || !password) {
        alert("Veuillez saisir votre identifiant et votre mot de passe.");
        return;
    }

    loginBtn.classList.add('loading');
    loginBtn.disabled = true;

    try {
        const resp = await fetch('/api/scolarite/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await resp.json();

        if (!resp.ok) {
            alert(`Erreur : ${data.error}`);
            return;
        }

        currentUser = data.user;
        showDashboard();
    } catch (e) {
        alert(`Erreur de connexion : ${e.message}`);
    } finally {
        loginBtn.classList.remove('loading');
        loginBtn.disabled = false;
    }
}

// Déconnexion
async function logout() {
    try {
        await fetch('/api/scolarite/logout', { method: 'POST' });
        currentUser = null;
        showLogin();
    } catch (e) {
        console.error("Erreur déconnexion:", e);
    }
}

// Afficher l'écran de login
function showLogin() {
    $('login-container').classList.remove('hidden');
    $('scolarite-dashboard').classList.add('hidden');
    $('scolarite-username').value = '';
    $('scolarite-password').value = '';
    
    // Animation de fade in sur la carte
    const card = document.querySelector('.login-container .scolarite-card');
    card.classList.remove('animate-fade-in-up');
    card.offsetHeight;
    card.classList.add('animate-fade-in-up');
}

// Afficher le dashboard et charger les données
async function showDashboard() {
    $('login-container').classList.add('hidden');
    $('scolarite-dashboard').classList.remove('hidden');

    $('user-display-name').textContent = currentUser.name;
    const roleLabels = { student: 'Élève / Étudiant', teacher: 'Enseignant / Professeur' };
    $('user-display-role').textContent = roleLabels[currentUser.role] || currentUser.role;
    $('user-avatar-placeholder').textContent = currentUser.name.charAt(0).toUpperCase();

    // Masquer/Afficher les vues spécifiques et gérer les boutons d'onglets selon le rôle
    if (currentUser.role === 'student') {
        $('student-results-view').classList.remove('hidden');
        $('teacher-results-view').classList.add('hidden');
        $('results-tab-label').textContent = 'Notes & Bulletins';
        $('tab-rh-btn').classList.add('hidden'); // Cacher l'onglet RH pour les étudiants
    } else if (currentUser.role === 'teacher') {
        $('student-results-view').classList.add('hidden');
        $('teacher-results-view').classList.remove('hidden');
        $('results-tab-label').textContent = 'Saisie des Notes';
        $('tab-rh-btn').classList.remove('hidden'); // Afficher l'onglet RH pour les enseignants
    }

    await loadDashboardData();

    // Reset default active tab on show
    const defaultTab = document.querySelector('.scolarite-tabs .tab-btn');
    if (defaultTab) defaultTab.click();
}

// Charger les données du dashboard depuis SQLite
async function loadDashboardData() {
    try {
        const resp = await fetch('/api/scolarite/dashboard');
        const data = await resp.json();

        if (!resp.ok) {
            console.error("Erreur de chargement des données:", data.error);
            return;
        }

        renderSchedule(data.schedules);
        renderMessages(data.messages);

        if (currentUser.role === 'student') {
            renderStudentGrades(data.grades);
            renderStudentBulletins(data.bulletins);
        } else if (currentUser.role === 'teacher') {
            renderTeacherStudentsSelect(data.students_list);
            renderTeacherGradesTable(data.class_grades);
            renderTeacherPayslips(data.payslips);
        }
    } catch (e) {
        console.error("Erreur de communication API:", e);
    }
}

// Rendre l'emploi du temps
function renderSchedule(schedules) {
    const grid = $('schedule-grid-container');
    grid.innerHTML = '';

    if (!schedules || !schedules.length) {
        grid.innerHTML = '<div class="text-muted">Aucun emploi du temps disponible.</div>';
        return;
    }

    // Créer les colonnes de jours
    schedules.forEach((sched, index) => {
        const col = document.createElement('div');
        col.className = 'schedule-col';
        col.style.animationDelay = `${index * 0.05}s`;
        col.classList.add('animate-fade-in-up');
        col.innerHTML = `
            <div class="schedule-day-header">${sched.day}</div>
            <div class="schedule-slot slot-morning">
                <span class="slot-time">08h00 - 11h00</span>
                <span class="slot-desc">${sched.slot1 || 'Aucun cours'}</span>
            </div>
            <div class="schedule-slot slot-midday">
                <span class="slot-time">11h00 - 13h00</span>
                <span class="slot-desc">${sched.slot2 || 'Aucun cours'}</span>
            </div>
            <div class="schedule-slot slot-afternoon">
                <span class="slot-time">14h00 - 17h00</span>
                <span class="slot-desc">${sched.slot3 || 'Aucun cours'}</span>
            </div>
        `;
        grid.appendChild(col);
    });
}

// Rendre les notes de l'étudiant
function renderStudentGrades(grades) {
    const tbody = $('student-grades-tbody');
    tbody.innerHTML = '';

    if (!grades || !grades.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Aucune note enregistrée.</td></tr>';
        return;
    }

    grades.forEach(g => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td data-label="Matière"><strong>${escapeHtml(g.subject)}</strong></td>
            <td data-label="Note"><span class="grade-badge">${g.grade.toFixed(2)} / 20</span></td>
            <td data-label="Coefficient" class="text-muted">Coeff. ${g.coefficient}</td>
            <td data-label="Date d'évaluation" class="text-muted">${g.date}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Rendre les bulletins de l'étudiant
function renderStudentBulletins(bulletins) {
    const list = $('student-bulletins-list');
    list.innerHTML = '';

    if (!bulletins || !bulletins.length) {
        list.innerHTML = '<div class="text-muted small">Aucun bulletin disponible.</div>';
        return;
    }

    bulletins.forEach(b => {
        const item = document.createElement('div');
        item.className = 'bulletin-item';
        item.innerHTML = `
            <div class="bulletin-info">
                <span class="bulletin-name">Bulletin ${escapeHtml(b.period)}</span>
                <span class="bulletin-meta text-muted">Moyenne Générale : ${b.gpa.toFixed(2)} / 20</span>
            </div>
            <a href="#" class="btn-download-bulletin" onclick="event.preventDefault(); alert('Téléchargement simulé : ${b.file_name}');">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            </a>
        `;
        list.appendChild(item);
    });
}

// Rendre les fiches de paie du professeur
function renderTeacherPayslips(payslips) {
    const list = $('teacher-payslips-list');
    list.innerHTML = '';

    if (!payslips || !payslips.length) {
        list.innerHTML = '<div class="text-muted small">Aucune fiche de paie disponible.</div>';
        return;
    }

    payslips.forEach(p => {
        const item = document.createElement('div');
        item.className = 'bulletin-item';
        item.innerHTML = `
            <div class="bulletin-info">
                <span class="bulletin-name">Fiche de salaire - ${escapeHtml(p.month)}</span>
                <span class="bulletin-meta text-muted">Montant versé : ${p.amount.toFixed(2)} €</span>
            </div>
            <a href="#" class="btn-download-bulletin" onclick="event.preventDefault(); alert('Téléchargement de la fiche de paie : ${p.file_name}');">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            </a>
        `;
        list.appendChild(item);
    });
}

// Rendre la liste de choix d'étudiants pour le professeur
function renderTeacherStudentsSelect(students) {
    const select = $('grade-student');
    select.innerHTML = '';

    if (!students || !students.length) return;

    students.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.username;
        opt.textContent = s.name;
        select.appendChild(opt);
    });
}

// Rendre le relevé complet des notes des élèves
function renderTeacherGradesTable(grades) {
    const tbody = $('teacher-grades-tbody');
    tbody.innerHTML = '';

    if (!grades || !grades.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Aucune note saisie.</td></tr>';
        return;
    }

    grades.forEach(g => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td data-label="Étudiant"><strong>${escapeHtml(g.student_name)}</strong> <span class="mono text-muted small">(${g.student_username})</span></td>
            <td data-label="Matière">${escapeHtml(g.subject)}</td>
            <td data-label="Note"><span class="grade-badge">${g.grade.toFixed(2)} / 20</span></td>
            <td data-label="Coefficient" class="text-muted">Coeff. ${g.coefficient}</td>
            <td data-label="Date" class="text-muted">${g.date}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Rendre l'historique des messages adressés à l'administration
function renderMessages(messages) {
    const list = $('messages-history-list');
    list.innerHTML = '';

    if (!messages || !messages.length) {
        list.innerHTML = '<div class="text-muted small">Aucun message envoyé.</div>';
        return;
    }

    messages.forEach(m => {
        const card = document.createElement('div');
        card.className = 'history-message-card';
        card.innerHTML = `
            <div class="msg-card-header">
                <span class="msg-subject">Objet : ${escapeHtml(m.subject)}</span>
                <span class="msg-date mono text-muted">${m.date}</span>
            </div>
            <div class="msg-card-body text-muted">${escapeHtml(m.message)}</div>
        `;
        list.appendChild(card);
    });
}

// Formulaire : Ajouter une note
async function addGrade(e) {
    e.preventDefault();

    const student_username = $('grade-student').value;
    const subject = $('grade-subject').value.trim();
    const grade = $('grade-value').value;
    const coefficient = $('grade-coeff').value;
    const submitBtn = e.target.querySelector('button[type="submit"]');

    submitBtn.disabled = true;

    try {
        const resp = await fetch('/api/scolarite/add-grade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_username, subject, grade, coefficient })
        });

        const data = await resp.json();

        if (!resp.ok) {
            alert(`Erreur : ${data.error}`);
            return;
        }

        $('grade-value').value = '';
        await loadDashboardData();
    } catch (err) {
        alert("Erreur réseau: " + err.message);
    } finally {
        submitBtn.disabled = false;
    }
}

// Formulaire : Envoyer un message à l'administration
async function sendAdminMessage(e) {
    e.preventDefault();

    const subject = $('msg-subject').value.trim();
    const message = $('msg-body').value.trim();
    const submitBtn = e.target.querySelector('button[type="submit"]');

    submitBtn.disabled = true;

    try {
        const resp = await fetch('/api/scolarite/send-message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ subject, message })
        });

        const data = await resp.json();

        if (!resp.ok) {
            alert(`Erreur : ${data.error}`);
            return;
        }

        $('msg-subject').value = '';
        $('msg-body').value = '';
        await loadDashboardData();
    } catch (err) {
        alert("Erreur réseau: " + err.message);
    } finally {
        submitBtn.disabled = false;
    }
}

// Échappement des caractères HTML pour la sécurité XSS
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;")
              .replace(/</g, "&lt;")
              .replace(/>/g, "&gt;")
              .replace(/"/g, "&quot;")
              .replace(/'/g, "&#039;");
}
