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
                if (e.key === 'v' || e.key === 'V') {
                    const btn = document.getElementById('hidden-v-btn');
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

                    cy.on('tap free', 'node, edge', function(evt) {
                        setTimeout(function() {
                            if (cy.$(':selected').length === 1) {
                                evt.target.unselect();
                            }
                        }, 10);
                    });

                    let tappedTimeout;
                    let tappedBefore;
                    cy.on('tap', 'node, edge', function(evt) {
                        let tappedNow = evt.target;
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
                    });
                }
            }, 500);
            
            return window.dash_clientside.no_update;
        }
    }
});