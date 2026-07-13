document.addEventListener('DOMContentLoaded', () => {
    // 1. Auth Tabs Logic (index.html)
    const tabLogin = document.getElementById('tab-login');
    const tabSignup = document.getElementById('tab-signup');
    const formLogin = document.getElementById('form-login');
    const formSignup = document.getElementById('form-signup');

    if (tabLogin && tabSignup) {
        tabLogin.addEventListener('click', () => {
            tabLogin.classList.add('active');
            tabSignup.classList.remove('active');
            formLogin.classList.add('active');
            formSignup.classList.remove('active');
        });

        tabSignup.addEventListener('click', () => {
            tabSignup.classList.add('active');
            tabLogin.classList.remove('active');
            formSignup.classList.add('active');
            formLogin.classList.remove('active');
        });
    }

    // 2. Drag & Drop Upload Logic (index.html)
    const dropZone = document.getElementById('id-drop-zone');
    const fileInput = document.getElementById('id-file');

    if (dropZone && fileInput) {
        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                dropZone.querySelector('p').textContent = e.dataTransfer.files[0].name;
                dropZone.querySelector('p').style.color = 'var(--neon-cyan)';
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                dropZone.querySelector('p').textContent = fileInput.files[0].name;
                dropZone.querySelector('p').style.color = 'var(--neon-cyan)';
            }
        });
    }

    // 3. Dashboard Logic (dashboard.html)
    const memberContainer = document.getElementById('member-list-container');
    const searchInput = document.getElementById('member-search');

    if (memberContainer) {
        // Load members
        const loadMembers = async (query = '') => {
            try {
                const res = await fetch(`/api/members?q=${query}`);
                const members = await res.json();
                renderMembers(members);
            } catch (err) {
                console.error("Erreur chargement membres:", err);
            }
        };

        const renderMembers = (members) => {
            memberContainer.innerHTML = '';
            if (members.length === 0) {
                memberContainer.innerHTML = '<p class="tech-text" style="text-align: center; margin-top: 1rem;">[ AUCUN_NOEUD_TROUVE ]</p>';
                return;
            }

            members.forEach(member => {
                const initial = member.name.charAt(0).toUpperCase();
                const statusClass = member.online ? 'online' : '';

                const card = document.createElement('div');
                card.className = 'member-card';
                card.innerHTML = `
                    <div class="member-avatar">
                        ${initial}
                        <div class="status-dot ${statusClass}"></div>
                    </div>
                    <div class="member-info">
                        <h4>${member.name}</h4>
                        <p>${member.role}</p>
                    </div>
                `;

                card.addEventListener('click', () => {
                    document.querySelectorAll('.member-card').forEach(c => c.classList.remove('active'));
                    card.classList.add('active');
                    openChat(member);
                });

                memberContainer.appendChild(card);
            });
        };

        // Search listener
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                loadMembers(e.target.value);
            });
        }

        // Chat logic
        const chatHeader = document.getElementById('chat-header-info');
        const chatMessages = document.getElementById('chat-messages-container');
        const chatInputArea = document.getElementById('chat-input-area');
        const messageInput = document.getElementById('message-input');
        const btnSend = document.getElementById('btn-send-message');
        const btnAttach = document.getElementById('btn-attach');
        const chatFileInput = document.getElementById('chat-file-input');

        let currentMemberId = null;

        const openChat = async (member) => {
            currentMemberId = member.id;
            // Update UI
            chatHeader.innerHTML = `
                <div class="member-avatar" style="margin-right: 1rem;">
                    ${member.name.charAt(0)}
                    <div class="status-dot ${member.online ? 'online' : ''}"></div>
                </div>
                <div>
                    <h3 style="margin: 0;">${member.name}</h3>
                    <p class="tech-text" style="margin: 0;">[ CANAL_CHIFFRÉ_E2E ]</p>
                </div>
            `;

            chatMessages.classList.remove('hidden');
            chatInputArea.classList.remove('hidden');
            chatMessages.innerHTML = '<p class="tech-text" style="text-align:center; margin-top: auto; margin-bottom: auto;">Déchiffrement en cours...</p>';

            // Load messages
            try {
                const res = await fetch(`/api/messages/${member.id}`);
                const messages = await res.json();
                renderMessages(messages);
            } catch (err) {
                console.error("Erreur chargement messages:", err);
            }
        };

        const renderMessages = (messages) => {
            chatMessages.innerHTML = '';
            if (messages.length === 0) {
                chatMessages.innerHTML = '<div class="tech-text" style="text-align: center; margin-top: auto; margin-bottom: auto;">[ CANAL_ÉTABLI - AUCUN_MESSAGE ]</div>';
                return;
            }

            messages.forEach(msg => {
                const isSentByMe = msg.sender === 'Me';
                const el = document.createElement('div');
                el.className = `message ${isSentByMe ? 'sent' : 'received'}`;

                let fileHtml = '';
                if (msg.file_url) {
                    const isImage = msg.file_name && msg.file_name.match(/\.(jpeg|jpg|gif|png)$/i);
                    if (isImage) {
                        fileHtml = `<div style="margin-top: 10px;"><img src="${msg.file_url}" alt="Attachment" style="max-width: 100%; border-radius: 8px;"></div>`;
                    } else {
                        fileHtml = `<div style="margin-top: 10px;"><a href="${msg.file_url}" target="_blank" style="color: var(--neon-cyan); text-decoration: none; font-weight: bold;">📄 Ouvrir ${msg.file_name}</a></div>`;
                    }
                }

                el.innerHTML = `
                    <div>${msg.text}</div>
                    ${fileHtml}
                    <div class="message-time">${msg.time}</div>
                `;
                chatMessages.appendChild(el);
            });

            // Scroll bottom
            setTimeout(() => {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 10);
        };

        const sendMessage = async (customText, fileUrl = null, fileName = null) => {
            const text = typeof customText === 'string' ? customText : messageInput.value.trim();
            if (!text && !fileUrl) return;

            const now = new Date();
            const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

            const newMsg = {
                sender: "Me",
                text: text,
                file_url: fileUrl,
                file_name: fileName,
                time: timeStr
            };

            // Post to backend
            if (currentMemberId) {
                await fetch(`/api/messages/${currentMemberId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newMsg)
                });
            }

            let fileHtml = '';
            if (fileUrl) {
                const isImage = fileName && fileName.match(/\.(jpeg|jpg|gif|png)$/i);
                if (isImage) {
                    fileHtml = `<div style="margin-top: 10px;"><img src="${fileUrl}" alt="Attachment" style="max-width: 100%; border-radius: 8px;"></div>`;
                } else {
                    fileHtml = `<div style="margin-top: 10px;"><a href="${fileUrl}" target="_blank" style="color: var(--neon-cyan); text-decoration: none; font-weight: bold;">📄 Ouvrir ${fileName}</a></div>`;
                }
            }

            const el = document.createElement('div');
            el.className = 'message sent';
            el.innerHTML = `
                <div>${text}</div>
                ${fileHtml}
                <div class="message-time">${timeStr}</div>
            `;

            // Remove empty state if present
            if (chatMessages.innerHTML.includes('[ CANAL_ÉTABLI')) {
                chatMessages.innerHTML = '';
            }

            chatMessages.appendChild(el);
            messageInput.value = '';

            setTimeout(() => {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 10);
        };

        if (btnAttach && chatFileInput) {
            btnAttach.addEventListener('click', () => {
                chatFileInput.click();
            });

            chatFileInput.addEventListener('change', async () => {
                if (chatFileInput.files.length) {
                    const file = chatFileInput.files[0];
                    const formData = new FormData();
                    formData.append('file', file);

                    try {
                        const response = await fetch('/api/upload', {
                            method: 'POST',
                            body: formData
                        });
                        const data = await response.json();
                        if (data.url) {
                            sendMessage('', data.url, data.filename);
                        }
                    } catch (error) {
                        console.error('Erreur upload:', error);
                    }
                }
            });
        }

        if (btnSend) {
            btnSend.addEventListener('click', sendMessage);
        }

        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });
        }

        // Init
        loadMembers();
    }
});
