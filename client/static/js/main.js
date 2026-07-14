/**
 * main.js — CampusAdmin Portal UI Logic
 */

'use strict';

const $ = (id) => document.getElementById(id);
const now = () => new Date().toLocaleTimeString('fr-FR', { hour12: false });

let pendingEnvelopeData = null; // Données en attente de confirmation d'envoi
let selectedFile = null;

// --- Journal de Synchronisation Réseau (Console) ---
const consoleBody = $('console-body');

function consoleClear() {
    consoleBody.innerHTML = '<div class="console-line mono text-muted"><span class="ts">--:--:--</span><span class="msg">[ Journal vidé ]</span></div>';
}

function consoleLog(message, type = '') {
    const types = { success: 'log-success', error: 'log-error', warn: 'log-warn', info: 'log-info' };
    const cls = types[type] || '';
    const line = document.createElement('div');
    line.className = `console-line mono ${cls}`;
    line.innerHTML = `<span class="ts">${now()}</span> <span class="msg">${message}</span>`;
    consoleBody.appendChild(line);
    consoleBody.scrollTop = consoleBody.scrollHeight;
}

function consoleLogs(logsArray) {
    if (!logsArray) return;
    logsArray.forEach(msg => {
        let type = '';
        const lower = msg.toLowerCase();
        if (lower.includes('alerte') || lower.includes('erreur') || lower.includes('invalide') || lower.includes('refusé')) type = 'error';
        else if (lower.includes('succès') || lower.includes('validée') || lower.includes('livré') || lower.includes('terminée')) type = 'success';
        else if (lower.includes('attention') || lower.includes('warning') || lower.includes('transmission')) type = 'warn';
        else if (lower.includes('chargé') || lower.includes('génération') || lower.includes('chiffrement') || lower.includes('déchiffrement') || lower.includes('calcul')) type = 'info';
        
        // Nettoyage de terminologie E2EE dans les logs utilisateur
        let cleanedMsg = msg
            .replace(/chiffré/gi, 'sécurisé')
            .replace(/chiffrement/gi, 'sécurisation')
            .replace(/déchiffrement/gi, 'vérification de conformité')
            .replace(/cryptographique/gi, 'réseau')
            .replace(/cle private/gi, 'certificat d\'appareil')
            .replace(/clé privée/gi, 'certificat d\'appareil')
            .replace(/cle public/gi, 'clé d\'intégrité')
            .replace(/clé publique/gi, 'clé d\'intégrité')
            .replace(/E2EE/g, 'HTTPS (RGPD)');

        consoleLog(cleanedMsg, type);
    });
}

// ---------------------------------------------------------------------------
// Initialisation au démarrage
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    setupSidebarTabs();
    setupAttachmentButton();

    // Charger l'IP et le mode depuis localStorage s'ils existent
    const storedIp = localStorage.getItem('secureshare_server_ip') || '192.168.168.23';
    const storedMode = localStorage.getItem('secureshare_mode') || 'direct';

    const loginIp = $('server-ip-input');
    const loginMode = $('connection-mode-input');
    const regIp = $('reg-server-ip-input');
    const regMode = $('reg-connection-mode-input');

    if (loginIp) loginIp.value = storedIp;
    if (loginMode) loginMode.value = storedMode;
    if (regIp) regIp.value = storedIp;
    if (regMode) regMode.value = storedMode;

    selectedMode = storedMode;

    // Synchronisation des champs entre Connexion et Inscription
    if (loginIp && regIp) {
        loginIp.addEventListener('input', (e) => {
            regIp.value = e.target.value;
        });
        regIp.addEventListener('input', (e) => {
            loginIp.value = e.target.value;
        });
    }

    if (loginMode && regMode) {
        loginMode.addEventListener('change', (e) => {
            regMode.value = e.target.value;
            selectedMode = e.target.value;
        });
        regMode.addEventListener('change', (e) => {
            loginMode.value = e.target.value;
            selectedMode = e.target.value;
        });
    }
});

// ---------------------------------------------------------------------------
// Écran d'Initialisation (Setup Overlay)
// ---------------------------------------------------------------------------
let selectedUser = '';
let selectedMode = 'direct';

// Gérer l'alternance d'onglets Connexion / Inscription
$('tab-login').addEventListener('click', () => {
    $('tab-login').classList.add('active');
    $('tab-register').classList.remove('active');
    $('form-login-container').classList.remove('hidden');
    $('form-register-container').classList.add('hidden');
});

$('tab-register').addEventListener('click', () => {
    $('tab-register').classList.add('active');
    $('tab-login').classList.remove('active');
    $('form-register-container').classList.remove('hidden');
    $('form-login-container').classList.add('hidden');
});

// Connexion
$('btn-launch').addEventListener('click', async () => {
    const username = $('username-input').value.trim().toLowerCase();
    const password = $('password-input').value.trim();
    const serverIp = ($('server-ip-input').value.trim()) || '127.0.0.1';
    const connectionMode = $('connection-mode-input').value;

    if (!username || !password) {
        alert('Veuillez entrer votre identifiant et votre mot de passe.');
        return;
    }
    selectedUser = username;
    selectedMode = connectionMode;

    // Sauvegarde pour le prochain chargement
    localStorage.setItem('secureshare_server_ip', serverIp);
    localStorage.setItem('secureshare_mode', connectionMode);

    const btn = $('btn-launch');

    btn.disabled = true;
    btn.textContent = 'Connexion...';

    try {
        const resp = await fetch('/api/local-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: selectedUser, password: password, server_ip: serverIp, mode: selectedMode })
        });

        if (!resp.ok) {
            const err = await resp.json();
            alert(`Erreur : ${err.error}`);
            return;
        }

        await loadDashboard();
        $('setup-overlay').classList.add('hidden');
        $('dashboard').classList.remove('hidden');
        consoleLog(`Session de travail '${selectedUser}' ouverte. Liaison réseau ${selectedMode.toUpperCase()} active (Serveur : ${serverIp}).`, 'success');

    } catch (e) {
        alert(`Erreur de liaison locale : ${e.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>Ouvrir la session administrative</span>';
    }
});

// Inscription
$('btn-register-submit').addEventListener('click', async () => {
    const username = $('reg-username-input').value.trim().toLowerCase();
    const name = $('reg-name-input').value.trim();
    const password = $('reg-password-input').value.trim();
    const role = $('reg-role-input').value;
    const serverIp = ($('reg-server-ip-input').value.trim()) || '127.0.0.1';
    const connectionMode = $('reg-connection-mode-input').value;

    if (!username || !name || !password || !role) {
        alert('Veuillez remplir tous les champs du formulaire.');
        return;
    }
    selectedUser = username;
    selectedMode = connectionMode;

    // Sauvegarde pour le prochain chargement
    localStorage.setItem('secureshare_server_ip', serverIp);
    localStorage.setItem('secureshare_mode', connectionMode);

    const btn = $('btn-register-submit');

    btn.disabled = true;
    btn.textContent = 'Génération de clés RSA...';

    try {
        const resp = await fetch('/api/local-register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: selectedUser, name: name, password: password, role: role, server_ip: serverIp, mode: selectedMode })
        });

        if (!resp.ok) {
            const err = await resp.json();
            alert(`Erreur : ${err.error}`);
            return;
        }

        await loadDashboard();
        $('setup-overlay').classList.add('hidden');
        $('dashboard').classList.remove('hidden');
        consoleLog(`Compte '${selectedUser}' créé. Session de travail ouverte. Liaison réseau ${selectedMode.toUpperCase()} active (Serveur : ${serverIp}).`, 'success');

    } catch (e) {
        alert(`Erreur d'inscription locale : ${e.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>Créer le compte & Générer les clés</span>';
    }
});

// Bouton déconnexion
$('btn-reset').addEventListener('click', () => {
    $('setup-overlay').classList.remove('hidden');
    $('dashboard').classList.add('hidden');
    consoleClear();
    $('inbox-list').innerHTML = '<div class="inbox-empty mono text-muted">[ Aucun document en attente de synchronisation ]</div>';
    $('send-fp-warning').classList.add('hidden');
    
    // Réinitialiser les champs et remettre l'onglet connexion par défaut
    $('username-input').value = '';
    $('password-input').value = '';
    $('reg-username-input').value = '';
    $('reg-name-input').value = '';
    $('reg-password-input').value = '';
    $('tab-login').click();
});

// ---------------------------------------------------------------------------
// Gestion de la Sidebar (Tabs Navigation)
// ---------------------------------------------------------------------------
function setupSidebarTabs() {
    document.querySelectorAll('.menu-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const viewId = btn.dataset.tab;
            
            // Switch active tab class
            document.querySelectorAll('.menu-tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Switch view with transition animations
            const views = document.querySelectorAll('.admin-view');
            views.forEach(v => v.classList.remove('show'));

            setTimeout(() => {
                views.forEach(v => v.classList.remove('active'));
                
                const targetView = $(viewId);
                targetView.classList.add('active');
                
                // Force reflow
                targetView.offsetHeight;
                
                targetView.classList.add('show');

                // Actions spéciales au chargement de l'onglet
                if (viewId === 'view-scolarite') {
                    loadAdminScolariteMessages();
                }
            }, 150);
        });
    });
}

// ---------------------------------------------------------------------------
// Chargement du Dashboard (Config)
// ---------------------------------------------------------------------------
async function loadDashboard() {
    const resp = await fetch('/api/local-status');
    const data = await resp.json();

    if (!data.configured) return;

    const username = data.username;
    const role = data.role || 'membre';
    const name = data.name || username.toUpperCase();

    // Mettre à jour les badges
    $('topbar-username').textContent = `SESSION: ${role.toUpperCase()}-${username.toUpperCase()}`;

    const modeLabels = { direct: 'LIAISON: DIRECT', dmz: 'LIAISON: ZONE DMZ', vpn: 'LIAISON: TUNNEL VPN' };
    $('mode-label').textContent = modeLabels[data.mode] || data.mode.toUpperCase();

    // Remplir les informations d'identité
    $('identity-avatar').textContent = username.charAt(0).toUpperCase();
    $('identity-name').textContent = name;
    
    // Rôle descriptif
    const roleLabels = { 
        directrice: "Directrice de l'Université (Validateur)", 
        comptable: "Comptable du Campus (RH/Finances)",
        secretaire: "Secrétaire Général",
        rh: "Responsable Ressources Humaines",
        gestionnaire: "Gestionnaire Informatique"
    };
    $('identity-role').textContent = roleLabels[role.toLowerCase()] || (role.charAt(0).toUpperCase() + role.slice(1));

    // Remplir l'identifiant d'appareil
    $('local-fingerprint').textContent = data.fingerprint || '----·----·----·----';

    // Remplir les configurations système
    $('cfg-server-ip').textContent = data.server_ip;
    $('cfg-mode').textContent = data.mode.toUpperCase();

    // Restreindre ou orienter par défaut les onglets selon l'utilisateur
    const composeTab = document.querySelector('.menu-tab-btn[data-tab="view-transfer"]');
    const inboxTab = document.querySelector('.menu-tab-btn[data-tab="view-inbox"]');

    if (role.toLowerCase() === 'directrice') {
        inboxTab.click();
        $('send-to').value = 'alice'; // Par défaut vers Alice
    } else {
        composeTab.click();
        $('send-to').value = 'bob'; // Par défaut vers la directrice
    }
}

// ---------------------------------------------------------------------------
// Gestion de la pièce jointe (Gmail-like)
// ---------------------------------------------------------------------------
function setupAttachmentButton() {
    const triggerBtn = $('btn-trigger-file');
    const fileInput = $('file-input');

    triggerBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            selectedFile = fileInput.files[0];
            $('file-selected').classList.remove('hidden');
            $('file-name-display').textContent = `📄 ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} Ko)`;
            consoleLog(`Pièce jointe sélectionnée : ${selectedFile.name}`, 'info');
        }
    });

    $('btn-clear-file').addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        $('file-selected').classList.add('hidden');
        consoleLog("Pièce jointe retirée.", 'info');
    });
}

// ---------------------------------------------------------------------------
// Envoi de Message Sécurisé (Gmail-like)
// ---------------------------------------------------------------------------
$('btn-send').addEventListener('click', async () => {
    const recipient = $('send-to').value.trim().toLowerCase();
    const subject = $('send-subject').value.trim();
    const messageBody = $('send-message').value.trim();
    const btn = $('btn-send');

    if (!recipient) {
        alert('Veuillez renseigner un destinataire.');
        return;
    }
    if (!subject && !messageBody && !selectedFile) {
        alert('Veuillez spécifier un objet, un message ou joindre un fichier.');
        return;
    }

    // On compile le sujet et le message pour le stockage
    const fullMessage = subject ? `Objet : ${subject}\n\n${messageBody}` : messageBody;

    consoleLog(`Lancement de l'enregistrement de document vers '${recipient}'...`, 'info');
    btn.disabled = true;
    btn.textContent = 'Sécurisation...';

    try {
        let payload = { to: recipient, message: fullMessage };

        if (selectedFile) {
            const fileB64 = await fileToBase64(selectedFile);
            payload.file_b64 = fileB64;
            payload.file_name = selectedFile.name;
        }

        const resp = await fetch('/api/local-send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await resp.json();
        consoleLogs(data.logs);

        if (!resp.ok) {
            consoleLog(`ERREUR : ${data.error}`, 'error');
            alert(`Erreur de transmission : ${data.error}`);
            return;
        }

        // Fenêtre de double validation
        pendingEnvelopeData = { payload, serverFP: data.server_fingerprint };
        $('send-server-fp').textContent = data.server_fingerprint;
        $('send-fp-warning').classList.remove('hidden');

        consoleLog(`Clé de registre d'appareil reçue : ${data.server_fingerprint}`, 'warn');

    } catch (e) {
        consoleLog(`Erreur réseau : ${e.message}`, 'error');
        alert(`Erreur réseau : ${e.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>Transmettre le document</span>';
    }
});

// Confirmation de conformité d'appareil
$('btn-confirm-send').addEventListener('click', () => {
    consoleLog('Empreinte d\'appareil validée par l\'opérateur.', 'success');
    $('send-fp-warning').classList.add('hidden');
    $('send-subject').value = '';
    $('send-message').value = '';
    
    if (selectedFile) {
        $('btn-clear-file').click();
    }
    
    pendingEnvelopeData = null;
    consoleLog('Document enregistré avec succès sur le serveur central.', 'success');
    alert('✅ Transfert sécurisé réussi.');
});

$('btn-cancel-send').addEventListener('click', () => {
    consoleLog('CONFORMITÉ : Transfert avorté par l\'opérateur pour discordance de clé.', 'error');
    $('send-fp-warning').classList.add('hidden');
    pendingEnvelopeData = null;
});

// Simulation d'erreur
$('btn-alter').addEventListener('click', async () => {
    consoleLog('[ DIAGNOSTIC ] Simulation d\'une altération réseau en transit...', 'warn');
    try {
        const resp = await fetch('/api/local-alter', { method: 'POST' });
        const data = await resp.json();
        if (!resp.ok) {
            consoleLog(`Erreur : ${data.error}`, 'error');
            return;
        }
        consoleLog("Un bit du document a été altéré à des fins de test.", 'warn');
        alert('✅ Simulation d\'erreur configurée. Ouvrez la boîte de réception de votre correspondant pour observer la détection automatique.');
    } catch (e) {
        consoleLog(`Erreur : ${e.message}`, 'error');
    }
});

// ---------------------------------------------------------------------------
// Réception & Validation de Documents
// ---------------------------------------------------------------------------
$('btn-refresh-inbox').addEventListener('click', async () => {
    const btn = $('btn-refresh-inbox');
    btn.disabled = true;
    btn.textContent = 'Synchronisation...';
    consoleLog('Lecture des paquets réseaux sur le serveur...', 'info');

    try {
        const resp = await fetch('/api/local-inbox');
        const data = await resp.json();

        consoleLogs(data.logs);

        if (!resp.ok) {
            consoleLog(`ERREUR : ${data.error}`, 'error');
            return;
        }

        renderMessages(data.messages || []);

    } catch (e) {
        consoleLog(`Erreur réseau : ${e.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>Vérifier les nouveaux documents</span>';
    }
});

function renderMessages(messages) {
    const list = $('inbox-list');

    if (!messages.length) {
        list.innerHTML = '<div class="inbox-empty mono text-muted">[ Aucun document en attente de synchronisation ]</div>';
        consoleLog('Aucune nouvelle donnée réseau.', '');
        return;
    }

    list.innerHTML = '';

    messages.forEach(msg => {
        const tpl = document.getElementById('tpl-message');
        const card = tpl.content.cloneNode(true);

        const isValid = msg.status === 'valid';
        const isError = msg.status === 'error';

        card.querySelector('.message-from').textContent = `POSTE SOURCE : ${(msg.from || '?').toUpperCase()}`;
        card.querySelector('.message-time').textContent = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString('fr-FR') : now();

        // Bannière d'intégrité / conformité
        const banner = card.querySelector('.integrity-banner');
        if (isValid) {
            banner.textContent = 'VALIDÉ — Certificat d\'appareil authentifié. Fichier intègre.';
            banner.className = 'integrity-banner valid';
            consoleLog('Validation réussie : Signature et intégrité certifiées.', 'success');
        } else if (isError) {
            banner.textContent = `ERREUR DE SYNCHRONISATION — ${msg.error || 'Fichier non lisible'}`;
            banner.className = 'integrity-banner tampered';
            consoleLog(`ERREUR LECTURE : ${msg.error}`, 'error');
        } else {
            banner.textContent = 'ALERTE DE CONFORMITÉ — Échec de signature ! Le fichier a été modifié en transit !';
            banner.className = 'integrity-banner tampered';
            consoleLog('ALERTE : Signature corrompue ! Le document n\'est pas fiable.', 'error');
        }

        // Corps du message
        const body = card.querySelector('.message-body');
        if (isValid && !isError) {
            if (msg.is_file) {
                body.innerHTML = `<p><strong>Pièce reçue :</strong> ${msg.file_name || 'document'}</p>
                    <a href="data:application/octet-stream;base64,${msg.content}" download="${msg.file_name || 'document_valide'}" class="btn-secondary small" style="display:inline-flex;align-items:center;gap:6px;margin-top:8px;text-decoration:none;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                        <span>Télécharger le document</span>
                    </a>`;
            } else {
                // Remplacer les retours à la ligne par des <br> pour garder la mise en page
                body.innerHTML = escapeHtml(msg.content || msg.message || '').replace(/\n/g, '<br>');
            }
        } else {
            body.innerHTML = `<span class="text-muted mono small">${isError ? msg.error : 'DOCUMENT BLOQUÉ : Échec des vérifications d\'intégrité de transfert.'}</span>`;
        }

        // Logs techniques dépliables
        const logsToggle = card.querySelector('.message-logs-toggle');
        const logsBox = card.querySelector('.message-logs');

        if (msg.logs && msg.logs.length) {
            logsBox.innerHTML = msg.logs.map(l => {
                let cleaned = l
                    .replace(/chiffré/gi, 'sécurisé')
                    .replace(/chiffrement/gi, 'sécurisation')
                    .replace(/déchiffrement/gi, 'vérification de conformité')
                    .replace(/clé privée/gi, 'certificat d\'appareil')
                    .replace(/clé publique/gi, 'clé d\'intégrité')
                    .replace(/E2EE/g, 'HTTPS (RGPD)');
                return `<div>${cleaned}</div>`;
            }).join('');
            
            logsToggle.addEventListener('click', () => {
                const open = !logsBox.classList.contains('hidden');
                logsBox.classList.toggle('hidden', open);
                logsToggle.textContent = (open ? 'Afficher' : 'Masquer') + ' les étapes de validation technique';
            });
        } else {
            logsToggle.classList.add('hidden');
        }

        list.appendChild(card);
    });

    consoleLog(`${messages.length} document(s) chargé(s) dans la boîte de réception.`, 'success');
}

// ---------------------------------------------------------------------------
// Chargement de la Messagerie Scolarité (SQLite non-chiffrée)
// ---------------------------------------------------------------------------
async function loadAdminScolariteMessages() {
    const tbody = $('admin-scolarite-messages-tbody');
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Chargement en cours...</td></tr>';

    try {
        const resp = await fetch('/api/admin/messages');
        const data = await resp.json();

        tbody.innerHTML = '';

        if (!resp.ok) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-red">Erreur : ${data.error}</td></tr>`;
            return;
        }

        if (!data.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Aucun message de scolarité dans la base.</td></tr>';
            return;
        }

        data.forEach(m => {
            const tr = document.createElement('tr');
            const roleLabels = { student: 'Étudiant', teacher: 'Enseignant' };
            tr.innerHTML = `
                <td><strong>${escapeHtml(m.sender_name)}</strong> <span class="mono text-muted small">(${m.from_username})</span></td>
                <td><span class="user-role-badge">${roleLabels[m.role] || m.role}</span></td>
                <td><strong>${escapeHtml(m.subject)}</strong></td>
                <td class="text-muted">${escapeHtml(m.message)}</td>
                <td class="mono text-muted">${m.date}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-red">Erreur réseau : ${e.message}</td></tr>`;
    }
}

// ---------------------------------------------------------------------------
// Vérification de Clé / Empreinte d'appareil à la demande
// ---------------------------------------------------------------------------
$('btn-check-fp').addEventListener('click', async () => {
    const user = $('mitm-user').value.trim().toLowerCase();
    if (!user) {
        alert('Entrez un nom d\'utilisateur.');
        return;
    }

    consoleLog(`Interrogation de l'annuaire réseau pour l'appareil '${user}'...`, 'info');

    try {
        const resp = await fetch(`/api/remote-fingerprint?user=${user}`);
        const data = await resp.json();

        $('mitm-result').classList.remove('hidden');

        if (!resp.ok) {
            $('mitm-fp-display').textContent = 'ERREUR : ' + data.error;
            $('mitm-status').textContent = '';
            consoleLog(`Identifiant introuvable : ${data.error}`, 'error');
            return;
        }

        const serverFP = data.fingerprint;
        $('mitm-fp-display').textContent = serverFP;
        $('mitm-status').textContent = '✓ Poste enregistré de manière intègre dans l\'annuaire central.';
        
        consoleLog(`Certificat pour '${user}' récupéré : ${serverFP}`, 'info');

    } catch (e) {
        consoleLog(`Erreur réseau : ${e.message}`, 'error');
    }
});

// Helpers
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;")
              .replace(/</g, "&lt;")
              .replace(/>/g, "&gt;")
              .replace(/"/g, "&quot;")
              .replace(/'/g, "&#039;");
}
