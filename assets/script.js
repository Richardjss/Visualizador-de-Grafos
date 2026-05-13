window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        setup_interactions: function(id) {
            if (window.interactions_setup) return window.dash_clientside.no_update;
            window.interactions_setup = true;

            document.addEventListener('contextmenu', event => event.preventDefault());

            function setDashInputValue(inputId, value) {
                let input = document.getElementById(inputId);
                if (!input) return;
                let nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                nativeInputValueSetter.call(input, value);
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }

            document.addEventListener('keydown', function(e) {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
                
                // Atalho: V (Criar Vértice)
                if (e.key === 'v' || e.key === 'V') {
                    const btn = document.getElementById('hidden-v-btn');
                    if (btn) btn.click();
                }

                // Atalho: E (Criar Aresta do vértice selecionado)
                if (e.key === 'e' || e.key === 'E') {
                    const btn = document.getElementById('hidden-e-btn');
                    if (btn) btn.click();
                }

                // Atalho: Ctrl + S (Salvar Grafo)
                if (e.ctrlKey && (e.key === 's' || e.key === 'S')) {
                    e.preventDefault();
                    const btn = document.getElementById('hidden-ctrl-s-btn');
                    if (btn) btn.click();
                }
            });

            let checkCy = setInterval(function() {
                let cy_el = document.getElementById(id);
                if (cy_el && cy_el._cyreg && cy_el._cyreg.cy) {
                    clearInterval(checkCy);
                    let cy = cy_el._cyreg.cy;
                    
                    cy.on('cxttap', 'node, edge', function(evt){
                        let target = evt.target;
                        let pos = evt.renderedPosition;
                        setDashInputValue('right-click-data', JSON.stringify({
                            id: target.id(), 
                            x: pos.x, 
                            y: pos.y,
                            is_node: target.isNode()
                        }));
                        document.getElementById('hidden-right-click-btn').click();
                    });

                    let tappedTimeout;
                    let tappedBefore;
                    cy.on('tap', function(evt) {
                        let tappedNow = evt.target;
                        
                        if (tappedNow === cy) {
                            setDashInputValue('right-click-data', JSON.stringify({bg_cancel: true}));
                            document.getElementById('hidden-right-click-btn').click();
                            return;
                        }

                        if (tappedTimeout && tappedBefore === tappedNow) {
                            clearTimeout(tappedTimeout);
                            tappedTimeout = null;
                            setDashInputValue('dbl-click-data', JSON.stringify({
                                id: tappedNow.id(), 
                                is_node: tappedNow.isNode(), 
                                current_val: tappedNow.isNode() ? tappedNow.data('label') : tappedNow.data('weight')
                            }));
                            document.getElementById('hidden-dbl-click-btn').click();
                        } else {
                            tappedTimeout = setTimeout(function(){ tappedTimeout = null; }, 300);
                            tappedBefore = tappedNow;
                        }
                        
                        if (tappedNow.isEdge()) {
                            setDashInputValue('right-click-data', JSON.stringify({bg_cancel: true}));
                            document.getElementById('hidden-right-click-btn').click();
                        }
                    });
                }
            }, 500);
            
            // --- LÓGICA DE REDIMENSIONAMENTO MANUAL ---
            let isResizing = false;

            document.addEventListener('mousedown', function(e) {
                if (e.target.id === 'sidebar-resizer') {
                    isResizing = true;
                    document.body.style.cursor = 'ew-resize';
                    document.body.style.userSelect = 'none'; 
                }
            });

            document.addEventListener('mousemove', function(e) {
                if (!isResizing) return;

                const sidebar = document.getElementById('anim-sidebar');
                if (!sidebar) return;

                let newWidth = window.innerWidth - e.clientX - 15;

                // Limite Mínimo: 300px | Limite Máximo: 45% da tela
                const maxWidth = window.innerWidth * 0.45; 
                
                if (newWidth > 300 && newWidth < maxWidth) {
                    sidebar.style.width = newWidth + 'px';
                    sidebar.classList.remove('maximized-sidebar');
                }
            });

            document.addEventListener('mouseup', function() {
                isResizing = false;
                document.body.style.cursor = 'default';
                document.body.style.userSelect = 'auto';
            });

            return window.dash_clientside.no_update;
        }
    }
});
