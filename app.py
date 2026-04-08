# app.py
import dash
from dash import Input, Output, State, ctx, html
from dash.exceptions import PreventUpdate
import json
import copy
import base64
from collections import deque
import math
import dash_bootstrap_components as dbc

from layout import create_layout
from config import *

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = create_layout()

app.clientside_callback(
    dash.ClientsideFunction(namespace='clientside', function_name='setup_interactions'),
    Output('hidden-v-btn', 'id'),
    Input('cyto-graph', 'id')
)

@app.callback(
    Output("menu-acoes", "style"), Output("menu-arquivo", "style"), Output("menu-grafos", "style"), Output("menu-algoritmos", "style"),
    Output("top-menu-overlay", "style"),
    Input("btn-toggle-acoes", "n_clicks"), Input("btn-toggle-arquivo", "n_clicks"), Input("btn-toggle-grafos", "n_clicks"), Input("btn-toggle-algoritmos", "n_clicks"),
    Input('btn-confirm-bfs', 'n_clicks'), Input('btn-confirm-dfs', 'n_clicks'),
    Input('top-menu-overlay', 'n_clicks'),
    Input('btn-grafo-custom-trigger', 'n_clicks'),
    State("menu-acoes", "style"), State("menu-arquivo", "style"), State("menu-grafos", "style"), State("menu-algoritmos", "style"),
    State('anim-steps', 'data'),
    prevent_initial_call=True
)
def toggle_top_menus(n_ac, n_ar, n_gr, n_al, bfs_ok, dfs_ok, click_overlay, btn_custom, st_ac, st_ar, st_gr, st_al, anim_steps):
    
    trigger = ctx.triggered_id 
    
    s_ac = st_ac.copy() if st_ac else {'display': 'none'}
    s_ar = st_ar.copy() if st_ar else {'display': 'none'}
    s_gr = st_gr.copy() if st_gr else {'display': 'none'}
    s_al = st_al.copy() if st_al else {'display': 'none'}
    
    overlay_off = {'display': 'none'}
    overlay_on = {'display': 'block', 'position': 'fixed', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 'zIndex': 900, 'backgroundColor': 'transparent'}

    if trigger in ['top-menu-overlay', 'btn-confirm-bfs', 'btn-confirm-dfs', 'btn-grafo-custom-trigger']:
        s_ac['display'] = s_ar['display'] = s_gr['display'] = s_al['display'] = 'none'
        return s_ac, s_ar, s_gr, s_al, overlay_off

    if anim_steps and len(anim_steps) > 0:
        raise PreventUpdate

    if trigger == 'btn-toggle-acoes':
        target = 'flex' if s_ac.get('display') == 'none' else 'none'
        s_ac['display'], s_ar['display'], s_gr['display'], s_al['display'] = target, 'none', 'none', 'none'
    elif trigger == 'btn-toggle-arquivo':
        target = 'flex' if s_ar.get('display') == 'none' else 'none'
        s_ac['display'], s_ar['display'], s_gr['display'], s_al['display'] = 'none', target, 'none', 'none'
    elif trigger == 'btn-toggle-grafos':
        target = 'flex' if s_gr.get('display') == 'none' else 'none'
        s_ac['display'], s_ar['display'], s_gr['display'], s_al['display'] = 'none', 'none', target, 'none'
    elif trigger == 'btn-toggle-algoritmos':
        target = 'flex' if s_al.get('display') == 'none' else 'none'
        s_ac['display'], s_ar['display'], s_gr['display'], s_al['display'] = 'none', 'none', 'none', target

    final_overlay = overlay_on if any(s['display'] == 'flex' for s in [s_ac, s_ar, s_gr, s_al]) else overlay_off
    return s_ac, s_ar, s_gr, s_al, final_overlay

# --- LÓGICA DA JANELA MODAL DE SALVAR ---
@app.callback(
    Output('save-modal', 'style'),
    Input('btn-salvar-modal-trigger', 'n_clicks'),
    Input('btn-cancel-save', 'n_clicks'),
    Input('btn-confirm-save', 'n_clicks'),
    State('save-modal', 'style'),
    prevent_initial_call=True
)
def toggle_save_modal(n_salvar, n_cancel, n_confirm, style):
    trigger = ctx.triggered_id
    new_style = style.copy() if style else {}
    if trigger == 'btn-salvar-modal-trigger':
        new_style['display'] = 'flex'
    else:
        new_style['display'] = 'none'
    return new_style


@app.callback(
    Output("download-grafo", "data"),
    Input("btn-confirm-save", "n_clicks"),
    State("save-filename", "value"),
    State("cyto-graph", "elements"),
    State("graph-props", "data"),
    prevent_initial_call=True
)
def salvar_grafo(n_clicks, filename, elements, props):
    if n_clicks == 0 or not elements: raise PreventUpdate
    
    nodes = [el for el in elements if 'source' not in el['data']]
    edges = [el for el in elements if 'source' in el['data'] and not el['data'].get('is_auto_reverse')]
    
    lines = [f"{len(nodes)} {len(edges)}"]
    
    for edge in edges:
        u = edge['data']['source']
        v = edge['data']['target']
        w = edge['data'].get('weight', '0')
        if props['is_weighted']:
            lines.append(f"{u} {v} {w}")
        else:
            lines.append(f"{u} {v}")
            
    lines.append("---METADADOS---")
    lines.append(f"Orientado: {props['is_directed']}")
    lines.append(f"Ponderado: {props['is_weighted']}")
    for node in nodes:
        nid = node['data']['id']
        x, y = node.get('position', {}).get('x', 400), node.get('position', {}).get('y', 300)
        lines.append(f"{nid} {x} {y}")
            
    content = "\n".join(lines)
    return dict(content=content, filename=f"{filename or 'grafo'}.txt")

# ==========================================
# LÓGICAS DA SELEÇÃO MÚLTIPLA E CAIXA AZUL
# ==========================================
@app.callback(
    Output('multi-select-panel', 'style'), Output('multi-select-text', 'children'),
    Input('cyto-graph', 'selectedNodeData'), Input('cyto-graph', 'selectedEdgeData'), 
    State('anim-steps', 'data'), prevent_initial_call=True
)
def toggle_multi_select(sel_nodes, sel_edges, anim_steps):
    if anim_steps and len(anim_steps) > 0: return {'display': 'none'}, ""
    
    total = (len(sel_nodes) if sel_nodes else 0) + (len(sel_edges) if sel_edges else 0)
    
    if total > 0:
        return {
            'display': 'flex', 'flexDirection': 'column', 'position': 'absolute', 
            'top': '80px', 'left': '50%', 'transform': 'translateX(-50%)', 
            'backgroundColor': 'rgba(255, 255, 255, 0.95)', 'padding': '12px 15px', 
            'borderRadius': '8px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.3)', 
            'zIndex': 2500, 'alignItems': 'center', 'gap': '12px', 
            'border': '2px solid #3498db', 'minWidth': '140px'
        }, f"{total} itens"
        
    return {'display': 'none'}, ""

app.clientside_callback(
    """function(n_clicks) { if (n_clicks) { var cy = document.getElementById('cyto-graph')._cyreg.cy; cy.elements().unselect(); } return window.dash_clientside.no_update; }""",
    Output('dummy-unselect', 'children'), Input('btn-cancel-multi', 'n_clicks'), prevent_initial_call=True
)

# --- MASTER CONTROLLER ---
@app.callback(
    Output('cyto-graph', 'elements'), Output('node-counter', 'data'), Output('action-state', 'data'),
    Output('context-menu', 'style'), Output('edge-context-menu', 'style'), Output('menu-overlay', 'style'),
    Output('selected-node', 'data'), Output('status-bar', 'children'), Output('status-bar', 'style'),
    Output('edit-modal', 'style'), Output('edit-input', 'value'), Output('btn-orientado', 'style'),
    Output('btn-ponderado', 'style'), Output('graph-props', 'data'), Output('upload-grafo', 'contents'), 
    
    Input('hidden-v-btn', 'n_clicks'), Input('hidden-right-click-btn', 'n_clicks'), Input('hidden-dbl-click-btn', 'n_clicks'),
    Input('cyto-graph', 'tapNode'), Input('btn-add-node', 'n_clicks'), Input('btn-add-edge', 'n_clicks'),
    Input('btn-rename', 'n_clicks'), Input('btn-delete', 'n_clicks'), Input('btn-close-menu', 'n_clicks'),
    Input('btn-rename-edge', 'n_clicks'), Input('btn-delete-edge', 'n_clicks'), Input('btn-close-edge-menu', 'n_clicks'), 
    Input('menu-overlay', 'n_clicks'), Input('btn-save-edit', 'n_clicks'), Input('btn-cancel-edit', 'n_clicks'),
    Input('btn-orientado', 'n_clicks'), Input('btn-ponderado', 'n_clicks'),
    Input('upload-grafo', 'contents'), Input('btn-limpar', 'n_clicks'), Input('btn-details', 'n_clicks'),
    Input('btn-delete-multi', 'n_clicks'),

    State('right-click-data', 'value'), State('dbl-click-data', 'value'), State('edit-input', 'value'),
    State('cyto-graph', 'elements'), State('node-counter', 'data'), State('action-state', 'data'),
    State('selected-node', 'data'), State('btn-orientado', 'style'), State('btn-ponderado', 'style'),
    State('graph-props', 'data'), State('anim-steps', 'data'), 
    State('cyto-graph', 'selectedNodeData'), State('cyto-graph', 'selectedEdgeData'),
    prevent_initial_call=True
)
def master_controller(v_clicks, rc_clicks, dbl_clicks, tap_node, btn_node, btn_edge, btn_rename, btn_del, btn_close, 
                      btn_ren_edge, btn_del_edge, btn_close_edge, 
                      overlay_click, btn_save, btn_cancel, btn_orientado_clicks, btn_ponderado_clicks, 
                      upload_contents, btn_limpar, btn_details, btn_multi_del,
                      rc_data, dbl_data, edit_val, elements, counter, state, selected, orient_style, pond_style, props, anim_steps,
                      sel_nodes, sel_edges):
    
    trigger = ctx.triggered_id

    # Ignora ações se a animação estiver rodando
    if anim_steps and len(anim_steps) > 0:
        if trigger in ['hidden-right-click-btn', 'hidden-dbl-click-btn', 'hidden-v-btn', 'cyto-graph', 'btn-delete-multi']:
            return [dash.no_update] * 15 

    hide_node_menu, hide_edge_menu, hide_overlay = {'display': 'none'}, {'display': 'none'}, {'display': 'none'}
    show_overlay = {'display': 'block', 'position': 'fixed', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 'zIndex': 999, 'cursor': 'default'}
    hide_status, hide_modal = {'display': 'none'}, {'display': 'none'}
    show_status = {'position': 'absolute', 'top': '10px', 'left': '50%', 'transform': 'translateX(-50%)', 'backgroundColor': '#2980b9', 'color': 'white', 'padding': '10px 20px', 'borderRadius': '20px', 'zIndex': 1000, 'fontWeight': 'bold', 'display': 'block'}

    # Apenas o estilo ativo e as propriedades padrão são necessários para o reset
    style_ativo = {**DROPDOWN_ITEM_STYLE, 'backgroundColor': '#444'} 
    props_padrao = {'is_directed': True, 'is_weighted': True}

    # ---> LÓGICA DE MULTI DELEÇÃO <---
    if trigger == 'btn-delete-multi':
        ids_to_delete = set()
        if sel_nodes: ids_to_delete.update([n['id'] for n in sel_nodes])
        if sel_edges: ids_to_delete.update([e['id'] for e in sel_edges])
            
        if ids_to_delete:
            new_elements = []
            for e in elements:
                eid = e['data']['id']
                src = e['data'].get('source')
                tgt = e['data'].get('target')
                if eid in ids_to_delete or src in ids_to_delete or tgt in ids_to_delete:
                    continue
                new_elements.append(e)
            elements = new_elements

        if not elements:
           
            return [], 1, {'mode': 'idle', 'source_node': None}, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", style_ativo, style_ativo, props_padrao, None
        
        return elements, counter, state, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update

    # ---> LÓGICA DO BOTÃO LIMPAR <---
    elif trigger == 'btn-limpar':
        
        return [], 1, {'mode': 'idle', 'source_node': None}, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", style_ativo, style_ativo, props_padrao, None

    # ---> LÓGICA DE DELEÇÃO UNITÁRIA <---
    elif trigger == 'btn-delete' and selected:
        new_elements = [e for e in elements if e['data'].get('id') != selected and e['data'].get('source') != selected and e['data'].get('target') != selected]
        if not new_elements:
            
            return [], 1, {'mode': 'idle', 'source_node': None}, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", style_ativo, style_ativo, props_padrao, None
        return new_elements, counter, state, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update
    
    elif trigger == 'upload-grafo':
        if not upload_contents: raise PreventUpdate 
        try:
            content_type, content_string = upload_contents.split(',')
            decoded = base64.b64decode(content_string).decode('utf-8')
            lines = decoded.strip().splitlines()
            if not lines: raise PreventUpdate
            
            new_props = {'is_directed': True, 'is_weighted': True} 
            temp_edges, pos, modo = [], {}, "arestas"
            
            for line in lines[1:]:
                if "---METADADOS---" in line:
                    modo = "metadados"
                    continue
                parts = line.split()
                if not parts: continue
                if modo == "arestas": 
                    temp_edges.append(parts)
                else:
                    # 1. PARSER BLINDADO: Só fica Falso se tiver escrito 'false' explicitamente.
                    if "Orientado:" in line: 
                        val = line.split(":", 1)[-1].strip().lower()
                        new_props['is_directed'] = (val != 'false')
                    elif "Ponderado:" in line: 
                        val = line.split(":", 1)[-1].strip().lower()
                        new_props['is_weighted'] = (val != 'false')
                    elif len(parts) >= 3: 
                        pos[parts[0]] = (float(parts[1]), float(parts[2]))

            new_elements, max_id = [], 1
            all_node_ids = set()
            
            for e in temp_edges:
                all_node_ids.add(e[0])          
                if len(e) >= 2:
                    all_node_ids.add(e[1])      
                    
            all_node_ids.update(pos.keys())
            
            nos_sem_posicao = [nid for nid in all_node_ids if nid not in pos]
            qtd_sem_pos = len(nos_sem_posicao)
            raio = max(200, qtd_sem_pos * 12) if qtd_sem_pos > 0 else 200

            for nid in all_node_ids:
                if nid in pos:
                    x, y = pos[nid]
                else:
                    idx = nos_sem_posicao.index(nid)
                    angle = (2 * math.pi * idx) / qtd_sem_pos
                    x = 400 + raio * math.cos(angle)
                    y = 300 + raio * math.sin(angle)
                
                new_elements.append({'data': {'id': nid, 'label': nid}, 'position': {'x': x, 'y': y}})
                if nid.isdigit(): max_id = max(max_id, int(nid) + 1)
            
            base_class = ''
            if not new_props['is_directed']: base_class += ' undirected'
            if not new_props['is_weighted']: base_class += ' unweighted'
            
            for e in temp_edges:
                if len(e) < 2:
                    continue
                    
                u, v = e[0], e[1]
                w = e[2] if len(e) >= 3 else '0'
                if not new_props['is_weighted']: w = '0'
                
                # 2. TRAVA ANTI-CLONAGEM: Verifica se a conexão já existe antes de criar
                ja_existe = False
                for el in new_elements:
                    if 'source' in el['data']:
                        if new_props['is_directed']:
                            if el['data']['source'] == u and el['data']['target'] == v:
                                ja_existe = True; break
                        else: # Se for Não Orientado, checa ida e volta
                            if (el['data']['source'] == u and el['data']['target'] == v) or \
                               (el['data']['source'] == v and el['data']['target'] == u):
                                ja_existe = True; break
                                
                if ja_existe:
                    continue # Se já existe, ignora e vai para a próxima linha do txt
                
                # Cria a conexão
                new_elements.append({'data': {'id': f'e_{u}_{v}', 'source': u, 'target': v, 'weight': w}, 'classes': base_class})
                
                # Cria aresta reversa se for não orientado
                if not new_props['is_directed'] and u != v:
                    new_elements.append({'data': {'id': f'e_{v}_{u}_auto', 'source': v, 'target': u, 'weight': w, 'is_auto_reverse': True}, 'classes': base_class})
            
            # 3. BÔNUS VISUAL: Atualiza as cores dos botões "Orientado/Ponderado" no menu conforme o arquivo carregado!
            novo_orient_style = {**DROPDOWN_ITEM_STYLE, 'backgroundColor': '#444' if new_props['is_directed'] else '#2980b9'}
            novo_pond_style = {**DROPDOWN_ITEM_STYLE, 'backgroundColor': '#444' if new_props['is_weighted'] else '#2980b9'}

            return new_elements, max_id, {'mode': 'idle', 'source_node': None}, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", novo_orient_style, novo_pond_style, new_props, None
            
        except Exception as e:
            print("Erro ao ler arquivo:", e)
            raise PreventUpdate

    elif trigger == 'btn-orientado':
        props['is_directed'] = not props['is_directed']
        new_elements = copy.deepcopy(elements)
        if not props['is_directed']:
            orient_style['backgroundColor'] = '#2980b9' 
            edges_to_add = []
            for el in new_elements:
                if 'source' in el['data'] and not el['data'].get('is_auto_reverse'):
                    s, t = el['data']['source'], el['data']['target']
                    el['classes'] = el.get('classes', '') + ' undirected'
                    if not any(e.get('data', {}).get('source') == t and e.get('data', {}).get('target') == s for e in new_elements):
                        edges_to_add.append({'data': {'id': f'e_{t}_{s}_auto', 'source': t, 'target': s, 'weight': '0', 'is_auto_reverse': True}, 'classes': el.get('classes', '')})
            new_elements.extend(edges_to_add)
        else:
            orient_style['backgroundColor'] = '#444'
            new_elements = [el for el in new_elements if not el.get('data', {}).get('is_auto_reverse')]
            for el in new_elements:
                if 'source' in el['data']: el['classes'] = el.get('classes', '').replace(' undirected', '')
        return new_elements, counter, state, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update

    elif trigger == 'btn-ponderado':
        props['is_weighted'] = not props['is_weighted']
        new_elements = copy.deepcopy(elements)
        
        # Define as cores mantendo o estilo original do menu
        if not props['is_weighted']:
            pond_style = {**DROPDOWN_ITEM_STYLE, 'backgroundColor': '#2980b9'}
            for el in new_elements:
                if 'source' in el['data']:
                    el['data']['weight'] = '0'
                    if 'unweighted' not in el.get('classes', ''):
                        el['classes'] = el.get('classes', '') + ' unweighted'
        else:
            pond_style = {**DROPDOWN_ITEM_STYLE, 'backgroundColor': '#444'}
            for el in new_elements:
                if 'source' in el['data']:
                    el['classes'] = el.get('classes', '').replace(' unweighted', '')
        
        return new_elements, counter, state, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update
    
    elif trigger == 'hidden-v-btn':
        elements.append({'data': {'id': str(counter), 'label': str(counter)}, 'position': {'x': 400, 'y': 300}})
        return elements, counter + 1, {'mode': 'idle', 'source_node': None}, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update

        
    elif trigger == 'hidden-right-click-btn' and rc_data:
        data = json.loads(rc_data)
        
        
        menu_style = {
            'display': 'block', 'position': 'absolute', 
            'top': f"{data['y']}px", 'left': f"{data['x'] + 20}px", 
            'zIndex': 2000, 'backgroundColor': 'white', 'padding': '8px', 
            'border': '1px solid #bdc3c7', 'borderRadius': '8px', 
            'boxShadow': '0px 4px 10px rgba(0,0,0,0.2)'
        }
        
        
        if data.get('is_node', True): 
            return elements, counter, state, menu_style, hide_edge_menu, show_overlay, data['id'], "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update
        else: 
            return elements, counter, state, hide_node_menu, menu_style, show_overlay, data['id'], "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update

    elif trigger == 'hidden-dbl-click-btn' and dbl_data:
        data = json.loads(dbl_data)
        modal_style = {'display': 'block', 'position': 'absolute', 'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)', 'zIndex': 2000, 'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0px 0px 15px rgba(0,0,0,0.3)'}
        return elements, counter, {'mode': 'editing', 'target_id': data['id']}, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, modal_style, str(data['current_val']), orient_style, pond_style, props, dash.no_update

    elif trigger in ['btn-rename', 'btn-rename-edge'] and selected:
        current_val = ""
        for el in elements:
            if el['data']['id'] == selected:
                current_val = el['data'].get('label', '') if 'source' not in el['data'] else el['data'].get('weight', '')
                break
        modal_style = {'display': 'block', 'position': 'absolute', 'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)', 'zIndex': 2000, 'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0px 0px 15px rgba(0,0,0,0.3)'}
        return elements, counter, {'mode': 'editing', 'target_id': selected}, hide_node_menu, hide_edge_menu, hide_overlay, selected, "", hide_status, modal_style, str(current_val), orient_style, pond_style, props, dash.no_update

    elif trigger == 'btn-save-edit':
        if state.get('mode') == 'editing':
            target_id, novo_nome = state.get('target_id'), str(edit_val).strip()
            if not novo_nome: return elements, counter, {'mode': 'idle', 'source_node': None}, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update
            new_elements = copy.deepcopy(elements)
            is_node = any(el['data']['id'] == target_id and 'source' not in el['data'] for el in new_elements)
                    
            if is_node:
                id_em_uso = any(e['data']['id'] == novo_nome for e in new_elements if 'source' not in e['data'])
                if not id_em_uso or novo_nome == target_id:
                    for el in new_elements:
                        if el['data']['id'] == target_id and 'source' not in el['data']:
                            el['data']['id'] = el['data']['label'] = novo_nome
                    for el in new_elements:
                        if 'source' in el['data']:
                            alterou = False
                            if el['data']['source'] == target_id: el['data']['source'] = novo_nome; alterou = True
                            if el['data']['target'] == target_id: el['data']['target'] = novo_nome; alterou = True
                            if alterou:
                                u, v = el['data']['source'], el['data']['target']
                                el['data']['id'] = f'e_{v}_{u}_auto' if el['data'].get('is_auto_reverse') else f'e_{u}_{v}'
            else:
                for el in new_elements:
                    if el['data']['id'] == target_id:
                        try:
                            val = float(edit_val)
                            el['data']['weight'] = str(int(val)) if val.is_integer() else str(val)
                        except (ValueError, TypeError): pass 
            elements = new_elements
        return elements, counter, {'mode': 'idle', 'source_node': None}, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update

    elif trigger in ['btn-cancel-edit', 'btn-close-menu', 'btn-close-edge-menu', 'menu-overlay', 'btn-details']:
        return elements, counter, {'mode': 'idle', 'source_node': None}, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update

    elif trigger == 'cyto-graph' and tap_node:
        node_id = tap_node['data']['id']
        if state['mode'] == 'adding_edge' and state['source_node']:
            source = state['source_node']
            new_elements = copy.deepcopy(elements)
            if not any(e.get('data', {}).get('source') == source and e.get('data', {}).get('target') == node_id for e in new_elements):
                base_class = (' undirected' if not props['is_directed'] else '') + (' unweighted' if not props['is_weighted'] else '')
                new_elements.append({'data': {'id': f'e_{source}_{node_id}', 'source': source, 'target': node_id, 'weight': '0'}, 'classes': base_class})
                if not props['is_directed'] and source != node_id:
                    if not any(e.get('data', {}).get('source') == node_id and e.get('data', {}).get('target') == source for e in new_elements):
                        new_elements.append({'data': {'id': f'e_{node_id}_{source}_auto', 'source': node_id, 'target': source, 'weight': '0', 'is_auto_reverse': True}, 'classes': base_class})
            return new_elements, counter, {'mode': 'idle', 'source_node': None}, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update

    elif trigger == 'btn-add-node' and selected:
        parent_pos = next((el['position'] for el in elements if el['data']['id'] == selected), {'x': 400, 'y': 300})
        elements.append({'data': {'id': str(counter), 'label': str(counter)}, 'position': {'x': parent_pos['x'], 'y': parent_pos['y'] + 80}})
        return elements, counter + 1, state, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update

    elif trigger == 'btn-add-edge' and selected:
        return elements, counter, {'mode': 'adding_edge', 'source_node': selected}, hide_node_menu, hide_edge_menu, hide_overlay, None, f"Clique no destino...", show_status, hide_modal, "", orient_style, pond_style, props, dash.no_update

    elif trigger == 'btn-delete' and selected:
        elements = [e for e in elements if e['data'].get('id') != selected and e['data'].get('source') != selected and e['data'].get('target') != selected]
        return elements, counter, state, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update
        
    elif trigger == 'btn-delete-edge' and selected:
        edge_to_del = next((e for e in elements if e['data'].get('id') == selected), None)
        if edge_to_del:
            s, t = edge_to_del['data'].get('source'), edge_to_del['data'].get('target')
            if not props['is_directed']:
                elements = [e for e in elements if not ((e['data'].get('source') == s and e['data'].get('target') == t) or (e['data'].get('source') == t and e['data'].get('target') == s))]
            else:
                elements = [e for e in elements if e['data'].get('id') != selected]
        return elements, counter, state, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update

    return elements, counter, state, hide_node_menu, hide_edge_menu, hide_overlay, selected, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update

# --- LÓGICA DO PAINEL DE INFORMAÇÕES ---
@app.callback(
    Output('info-panel', 'style'),
    Output('info-panel-content', 'children'),
    Input('btn-info', 'n_clicks'),
    Input('btn-confirm-bfs', 'n_clicks'), Input('btn-confirm-dfs', 'n_clicks'), # Gatilhos
    Input('cyto-graph', 'elements'),
    Input('graph-props', 'data'),
    State('info-panel', 'style'),
    State('anim-steps', 'data'),
    prevent_initial_call=True
)
def atualizar_painel_info(n_clicks, bfs_ok, dfs_ok, elements, props, current_style, anim_steps):
    trigger = ctx.triggered_id
    new_style = current_style.copy() if current_style else {}
    
    if trigger in ['btn-confirm-bfs', 'btn-confirm-dfs']:
        new_style['display'] = 'none'
        return new_style, dash.no_update
    
    if trigger == 'btn-info':
        if anim_steps and len(anim_steps) > 0: raise PreventUpdate
        new_style['display'] = 'block' if new_style.get('display') == 'none' else 'none'
        
    if new_style.get('display') == 'none':
        return new_style, dash.no_update

    elements = elements or []
    nodes = [el for el in elements if 'source' not in el['data']]
    edges = [el for el in elements if 'source' in el['data'] and not el['data'].get('is_auto_reverse')]
    v_count = len(nodes)
    e_count = len(edges)
    is_dir = props.get('is_directed', True)
    is_weight = props.get('is_weighted', True)
    
    nos_conectados = set()
    for e in edges:
        nos_conectados.add(e['data']['source'])
        nos_conectados.add(e['data']['target'])
    isolados = v_count - len(nos_conectados)
            
    conteudo = [
        html.H3("Detalhes do Grafo", style={'marginTop': '0', 'borderBottom': '2px solid #2980b9', 'paddingBottom': '10px', 'color': '#2c3e50'}),
        html.P([html.B("Vértices: "), str(v_count)], style={'margin': '5px 0'}),
        html.P([html.B("Arestas: "), str(e_count)], style={'margin': '5px 0'}),
        html.P([html.B("Orientação: "), "Orientado" if is_dir else "Não Orientado"], style={'margin': '5px 0'}),
        html.P([html.B("Pesos: "), "Ponderado" if is_weight else "Não Ponderado"], style={'margin': '5px 0'}),
        html.P([html.B("Nós Isolados: "), str(isolados)], style={'margin': '5px 0'})
    ]
    
    if v_count <= 30 and e_count > 0:
        conteudo.append(html.H4("Conexões:", style={'marginTop': '20px', 'marginBottom': '10px', 'color': '#2c3e50'}))
        lista_conexoes = []
        for e in edges:
            u = e['data']['source']
            v = e['data']['target']
            w = e['data'].get('weight', '0')
            simbolo = "→" if is_dir else "—"
            texto = f"{u} {simbolo} {v} (Peso: {w})" 
            lista_conexoes.append(html.Li(texto, style={'marginBottom': '3px'}))
        conteudo.append(html.Ul(lista_conexoes, style={'paddingLeft': '20px', 'margin': '0', 'fontSize': '14px', 'color': '#34495e'}))
    elif v_count > 30:
        conteudo.append(html.P(html.I("A lista de conexões foi ocultada pois o grafo possui mais de 30 vértices."), style={'marginTop': '20px', 'color': '#7f8c8d', 'fontSize': '13px', 'textAlign': 'center'}))
    return new_style, conteudo

# --- LÓGICA DO MODAL DE DETALHES INDIVIDUAL ---
@app.callback(
    Output('vertex-details-modal', 'style'),
    Output('details-title', 'children'),
    Output('details-content', 'children'),
    Input('btn-details', 'n_clicks'),
    Input('btn-close-details', 'n_clicks'),
    State('selected-node', 'data'),
    State('cyto-graph', 'elements'),
    State('graph-props', 'data'),
    prevent_initial_call=True
)
def controlar_detalhes_vertice(n_abrir, n_fechar, selected, elements, props):
    trigger = ctx.triggered_id
    
    if trigger == 'btn-close-details' or not selected:
        return {'display': 'none'}, "", ""
    
    is_dir = props.get('is_directed', True)
    is_weight = props.get('is_weighted', True)
    
    edges = [el for el in elements if 'source' in el['data'] and not el['data'].get('is_auto_reverse')]
    
    def formatar_lista(lista_arestas):
        if not lista_arestas:
            return [html.P("Nenhuma conexão.", style={'color': '#7f8c8d', 'fontSize': '14px'})]
        
        itens = []
        for e in lista_arestas:
            origem = e['data']['source']
            destino = e['data']['target']
            peso = e['data'].get('weight', '0')
            simbolo = "→" if is_dir else "—"
            
            label = f"{origem} {simbolo} {destino} (Peso: {peso})"
            itens.append(html.Li(label))
        return [html.Ul(itens, style={'paddingLeft': '20px', 'margin': '5px 0'})]
    
    # SEPARAÇÃO LÓGICA: Orientado vs Não Orientado
    if is_dir:
        saida = [e for e in edges if e['data']['source'] == selected]
        entrada = [e for e in edges if e['data']['target'] == selected]
        conteudo = [
            html.H4("Saída", style={'marginBottom': '5px'}),
            *formatar_lista(saida),
            html.H4("Entrada", style={'marginTop': '15px', 'marginBottom': '5px'}),
            *formatar_lista(entrada)
        ]
    else:
        # Se for Não Orientado, junta todas as arestas que tocam neste vértice
        conexoes = [e for e in edges if e['data']['source'] == selected or e['data']['target'] == selected]
        conteudo = [
            html.H4("Conexões Bidirecionais", style={'marginBottom': '5px'}),
            *formatar_lista(conexoes)
        ]

    estilo_modal = {
        'display': 'flex', 'flexDirection': 'column', 'position': 'absolute', 
        'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)', 
        'zIndex': 3000, 'backgroundColor': 'white', 'padding': '25px', 
        'borderRadius': '8px', 'boxShadow': '0px 0px 20px rgba(0,0,0,0.4)', 
        'minWidth': '320px', 'maxHeight': '85vh'
    }

    conteudo_rolavel = html.Div(conteudo, style={'overflowY': 'auto', 'maxHeight': '60vh', 'paddingRight': '10px'})

    return estilo_modal, f"Vértice: {selected}", conteudo_rolavel

# ==========================================
# 1. FECHAR MODAIS AUTOMATICAMENTE
# ==========================================
@app.callback(
    Output('bfs-modal', 'style', allow_duplicate=True),
    Input('btn-bfs', 'n_clicks'), Input('btn-cancel-bfs', 'n_clicks'), Input('btn-confirm-bfs', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_bfs_modal(btn, cancel, confirm):
    if ctx.triggered_id == 'btn-bfs':
        return {'display': 'flex', 'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 'backgroundColor': 'rgba(0,0,0,0.5)', 'zIndex': 3000, 'alignItems': 'center', 'justifyContent': 'center'}
    return {'display': 'none'}

@app.callback(
    Output('dfs-modal', 'style', allow_duplicate=True),
    Input('btn-dfs', 'n_clicks'), Input('btn-cancel-dfs', 'n_clicks'), Input('btn-confirm-dfs', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_dfs_modal(btn, cancel, confirm):
    if ctx.triggered_id == 'btn-dfs':
        return {'display': 'flex', 'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 'backgroundColor': 'rgba(0,0,0,0.5)', 'zIndex': 3000, 'alignItems': 'center', 'justifyContent': 'center'}
    return {'display': 'none'}


# ==========================================
# 2. GERADORES DOS ROTEIROS (STEPS) DE ANIMAÇÃO
# ==========================================
@app.callback(
    Output('anim-steps', 'data'),
    Output('anim-index', 'data'),
    Output('anim-interval', 'disabled'),
    Output('anim-block-overlay', 'style'),
    Input('btn-confirm-bfs', 'n_clicks'),
    Input('btn-confirm-dfs', 'n_clicks'),
    State('bfs-start-node', 'value'),
    State('dfs-start-node', 'value'),
    State('cyto-graph', 'elements'),
    prevent_initial_call=True
)
def gerar_roteiro_animacao(bfs_click, dfs_click, bfs_start, dfs_start, elements):
    trigger = ctx.triggered_id
    start_node = bfs_start if trigger == 'btn-confirm-bfs' else dfs_start
    if not start_node or not elements: raise PreventUpdate

    start_node = str(start_node).strip()
    
    # NOVA TRAVA BFS/DFS: Se o vértice digitado não existir, cancela e não faz nada!
    exists = any(el['data']['id'] == start_node for el in elements if 'source' not in el['data'])
    if not exists:
        raise PreventUpdate

    adj_list = {el['data']['id']: [] for el in elements if 'source' not in el['data']}
    for el in elements:
        if 'source' in el['data']:
            u, v = el['data']['source'], el['data']['target']
            adj_list[u].append(v)
    for u in adj_list:
        try: adj_list[u].sort(key=lambda x: int(x))
        except ValueError: adj_list[u].sort()

    steps, visited = [], []
    
    if trigger == 'btn-confirm-bfs':
        fila = [start_node]
        enqueued = {start_node}
        steps.append({'current': None, 'visited': [], 'frontier': list(fila), 'ordem': []})
        
        while fila:
            current = fila.pop(0)
            steps.append({'current': current, 'visited': list(visited), 'frontier': list(fila), 'ordem': list(visited)})
            for vizinho in adj_list.get(current, []):
                if vizinho not in enqueued:
                    enqueued.add(vizinho)
                    fila.append(vizinho)
            steps.append({'current': current, 'visited': list(visited), 'frontier': list(fila), 'ordem': list(visited)})
            visited.append(current)
            
    elif trigger == 'btn-confirm-dfs':
        pilha = [start_node]
        steps.append({'current': None, 'visited': [], 'frontier': list(pilha), 'ordem': []})
        
        while pilha:
            current = pilha.pop()
            if current not in visited:
                steps.append({'current': current, 'visited': list(visited), 'frontier': list(pilha), 'ordem': list(visited)})
                for vizinho in reversed(adj_list.get(current, [])):
                    if vizinho not in visited:
                        pilha.append(vizinho)
                steps.append({'current': current, 'visited': list(visited), 'frontier': list(pilha), 'ordem': list(visited)})
                visited.append(current)

    steps.append({'current': None, 'visited': list(visited), 'frontier': [], 'ordem': list(visited)})
    
    overlay_style = {'display': 'block', 'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '70px', 'zIndex': 1500, 'backgroundColor': 'transparent', 'cursor': 'not-allowed'}
    
    return steps, 0, False, overlay_style


# ==========================================
# 3. CONTROLADOR DOS BOTÕES DO PLAYER
# ==========================================
@app.callback(
    Output('anim-index', 'data', allow_duplicate=True),
    Output('anim-interval', 'disabled', allow_duplicate=True),
    Output('btn-anim-play', 'children'),
    Input('btn-anim-start', 'n_clicks'), Input('btn-anim-prev', 'n_clicks'),
    Input('btn-anim-play', 'n_clicks'), Input('btn-anim-next', 'n_clicks'),
    Input('btn-anim-end', 'n_clicks'), Input('anim-interval', 'n_intervals'),
    State('anim-index', 'data'), State('anim-steps', 'data'), State('anim-interval', 'disabled'),
    prevent_initial_call=True
)
def player_controller(b1, b2, b3, b4, b5, n_int, idx, steps, is_disabled):
    trigger = ctx.triggered_id
    if not steps: return 0, True, '▶️'
    max_idx = len(steps) - 1
    
    if trigger == 'btn-anim-start': return 0, True, '▶️'
    elif trigger == 'btn-anim-end': return max_idx, True, '▶️'
    elif trigger == 'btn-anim-prev': return max(0, idx - 1), True, '▶️'
    elif trigger == 'btn-anim-next': return min(max_idx, idx + 1), True, '▶️'
    elif trigger == 'btn-anim-play':
        if is_disabled: return (0 if idx >= max_idx else idx), False, '⏸'
        else: return idx, True, '▶️'
    elif trigger == 'anim-interval':
        if idx < max_idx: return idx + 1, False, '⏸'
        else: return max_idx, True, '▶️'
        
    return idx, is_disabled, ('⏸' if not is_disabled else '▶️')


# ==========================================
# 4. MOTOR DE RENDERIZAÇÃO (PINTA O GRAFO E A TABELA)
# ==========================================
@app.callback(
    Output('cyto-graph', 'elements', allow_duplicate=True),
    Output('status-bar', 'children', allow_duplicate=True),
    Output('status-bar', 'style', allow_duplicate=True),
    Output('anim-player', 'style', allow_duplicate=True),
    Output('btn-close-anim', 'style', allow_duplicate=True),
    Output('anim-sidebar', 'style', allow_duplicate=True),
    Output('anim-sidebar-content', 'children'),
    Input('anim-index', 'data'),
    State('anim-steps', 'data'),
    State('cyto-graph', 'elements'),
    prevent_initial_call=True
)
def renderizar_animacao(idx, steps, elements):
    if not steps: raise PreventUpdate
    
    step_data = steps[idx]
    current = step_data.get('current')
    visited = step_data.get('visited', [])
    frontier = step_data.get('frontier', [])
    ordem = step_data.get('ordem', [])
    
    new_elements = copy.deepcopy(elements)
    for el in new_elements:
        base = el.get('classes', '').replace(' visited', '').replace(' frontier', '').replace(' current', '')
        el['classes'] = base
        if 'source' not in el['data']:
            nid = el['data']['id']
            if nid == current: el['classes'] += ' current'
            elif nid in visited: el['classes'] += ' visited'
            elif nid in frontier: el['classes'] += ' frontier'

    is_end = (idx == len(steps) - 1)
    status_text = " ➔ ".join(ordem)
    
    status_msg = f"Analisando: {current} | Caminho: {status_text}" if current else f"Caminho: {status_text}"
    status_style = {
        'position': 'absolute', 'top': '15px', 'left': '50%', 'transform': 'translateX(-50%)', 
        'backgroundColor': '#34495e', 'color': 'white', 'padding': '12px 25px', 
        'borderRadius': '30px', 'zIndex': 4000, 'fontWeight': 'bold', 'display': 'block', 
        'boxShadow': '0 4px 10px rgba(0,0,0,0.3)'
    }
    
    close_btn_style = {
        'display': 'flex', 'position': 'absolute', 'top': '70px', 'left': '50%', 'transform': 'translateX(-50%)',
        'backgroundColor': 'white', 'color': '#e74c3c', 'border': '2px solid #e74c3c', 'borderRadius': '50%',
        'width': '35px', 'height': '35px', 'fontSize': '18px', 'cursor': 'pointer', 'zIndex': 4000,
        'alignItems': 'center', 'justifyContent': 'center', 'boxShadow': '0 4px 10px rgba(0,0,0,0.3)', 'fontWeight': 'bold'
    }
    
    if is_end:
        status_style['backgroundColor'] = '#27ae60'
        status_msg = f"✅ Concluído! Ordem final: {status_text}"

    player_style = {
        'display': 'flex', 'position': 'absolute', 'bottom': '20px', 'left': '50%', 'transform': 'translateX(-50%)',
        'backgroundColor': '#111', 'padding': '10px 25px', 'borderRadius': '30px',
        'boxShadow': '0 4px 15px rgba(0,0,0,0.6)', 'zIndex': 2000, 'alignItems': 'center', 'gap': '20px'
    }

    sidebar_style = {
        'display': 'block', 'position': 'absolute', 'top': '15px', 'right': '15px',
        'backgroundColor': 'rgba(255, 255, 255, 0.95)', 'padding': '20px', 'borderRadius': '8px',
        'boxShadow': '0 4px 15px rgba(0,0,0,0.4)', 'zIndex': 2000, 'minWidth': '220px',
        'maxWidth': '300px', 'maxHeight': '80%', 'overflowY': 'auto', 'border': '1px solid #bdc3c7'
    }

    # Função auxiliar para desenhar as caixinhas coloridas com a mesma cor do grafo
    def badge(texto, cor):
        return html.Span(texto, style={'backgroundColor': cor, 'color': 'white', 'padding': '4px 10px', 'borderRadius': '12px', 'marginRight': '5px', 'marginBottom': '5px', 'display': 'inline-block', 'fontWeight': 'bold', 'fontSize': '14px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.2)'})

    # Preparando as listas da tabela baseadas no que está acontecendo nesse exato frame
    badge_atual = badge(current, '#e74c3c') if current else html.Span("Nenhum", style={'color': '#7f8c8d', 'fontStyle': 'italic'})
    badges_fronteira = [badge(v, '#f39c12') for v in frontier] if frontier else [html.Span("Vazia", style={'color': '#7f8c8d', 'fontStyle': 'italic'})]
    badges_visitados = [badge(v, '#27ae60') for v in visited] if visited else [html.Span("Nenhum", style={'color': '#7f8c8d', 'fontStyle': 'italic'})]

    sidebar_content = [
        html.Div([html.B("📌 Vértice Atual:", style={'color': '#333', 'display': 'block', 'marginBottom': '5px'}), badge_atual], style={'marginBottom': '20px'}),
        html.Div([html.B("⏳ Fila / Pilha:", style={'color': '#333', 'display': 'block', 'marginBottom': '5px'}), html.Div(badges_fronteira)], style={'marginBottom': '20px', 'borderLeft': '3px solid #f39c12', 'paddingLeft': '10px'}),
        html.Div([html.B("✅ Visitados (Prontos):", style={'color': '#333', 'display': 'block', 'marginBottom': '5px'}), html.Div(badges_visitados)], style={'borderLeft': '3px solid #27ae60', 'paddingLeft': '10px'})
    ]

    return new_elements, status_msg, status_style, player_style, close_btn_style, sidebar_style, sidebar_content


# ==========================================
# 5. SAIR DA ANIMAÇÃO E VOLTAR AO NORMAL
# ==========================================
@app.callback(
    Output('cyto-graph', 'elements', allow_duplicate=True),
    Output('anim-steps', 'data', allow_duplicate=True),
    Output('anim-player', 'style', allow_duplicate=True),
    Output('status-bar', 'style', allow_duplicate=True),
    Output('btn-close-anim', 'style', allow_duplicate=True),
    Output('anim-block-overlay', 'style', allow_duplicate=True),
    Output('anim-interval', 'disabled', allow_duplicate=True),
    Output('anim-sidebar', 'style', allow_duplicate=True),
    Input('btn-close-anim', 'n_clicks'),
    State('cyto-graph', 'elements'),
    prevent_initial_call=True
)
def fechar_animacao(n_clicks, elements):
    if not n_clicks: raise PreventUpdate
    
    new_elements = copy.deepcopy(elements)
    for el in new_elements:
        el['classes'] = el.get('classes', '').replace(' visited', '').replace(' frontier', '').replace(' current', '')
        
    return new_elements, [], {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, True, {'display': 'none'}

app.clientside_callback(
    """
    function(slider_val, cyto_zoom) {
        const ctx = dash_clientside.callback_context;
        if (!ctx.triggered.length) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }
        
        const trigger = ctx.triggered[0].prop_id;
        
        if (trigger === 'zoom-slider.value') {
            return [slider_val, window.dash_clientside.no_update];
        } else if (trigger === 'cyto-graph.zoom') {
            return [window.dash_clientside.no_update, cyto_zoom];
        }
        
        return [window.dash_clientside.no_update, window.dash_clientside.no_update];
    }
    """,
    Output('cyto-graph', 'zoom'),
    Output('zoom-slider', 'value'),
    Input('zoom-slider', 'value'),
    Input('cyto-graph', 'zoom'),
    prevent_initial_call=True
)

# ==========================================
# LÓGICA DO MODAL DE ADICIONAR VÉRTICE
# ==========================================
@app.callback(
    Output('add-node-modal', 'style', allow_duplicate=True),
    Output('add-node-id', 'value'),
    Output('add-node-connect-to', 'value'),
    Output('add-node-weight', 'value'),
    Output('add-node-error', 'children'),
    Output('cyto-graph', 'elements', allow_duplicate=True),
    Output('node-counter', 'data', allow_duplicate=True),
    
    Input('btn-add-node-menu', 'n_clicks'),
    Input('btn-cancel-add-node', 'n_clicks'),
    Input('btn-save-add-node', 'n_clicks'),
    
    State('add-node-modal', 'style'),
    State('add-node-id', 'value'),
    State('add-node-connect-to', 'value'),
    State('add-node-weight', 'value'),
    State('cyto-graph', 'elements'),
    State('node-counter', 'data'),
    State('graph-props', 'data'),
    prevent_initial_call=True
)
def gerenciar_modal_add_node(n_abrir, n_cancelar, n_salvar, style, node_id, connect_to, weight, elements, counter, props):
    trigger = ctx.triggered_id
    new_style = style.copy() if style else {}

    if trigger == 'btn-add-node-menu':
        new_style['display'] = 'flex'
        return new_style, str(counter), None, "", "", dash.no_update, dash.no_update

    elif trigger == 'btn-cancel-add-node':
        new_style['display'] = 'none'
        return new_style, "", None, "", "", dash.no_update, dash.no_update

    elif trigger == 'btn-save-add-node':
        if not node_id:
            return new_style, node_id, connect_to, weight, "⚠️ O nome não pode ser vazio.", dash.no_update, dash.no_update

        node_id = str(node_id).strip()
        
        # 1. Valida se o vértice sendo criado já existe
        exists = any(el['data']['id'] == node_id for el in elements if 'source' not in el['data'])
        if exists:
            return new_style, node_id, connect_to, weight, f"⚠️ O vértice '{node_id}' já existe!", dash.no_update, dash.no_update

        # 2. A NOVA TRAVA: Valida se o destino digitado realmente existe
        if connect_to:
            connect_to = str(connect_to).strip()
            dest_exists = any(el['data']['id'] == connect_to for el in elements if 'source' not in el['data'])
            if not dest_exists:
                return new_style, node_id, connect_to, weight, f"⚠️ O vértice destino '{connect_to}' não existe!", dash.no_update, dash.no_update

        new_elements = copy.deepcopy(elements)
        new_elements.append({'data': {'id': node_id, 'label': node_id}, 'position': {'x': 400, 'y': 300}})

        # 3. Cria a Aresta 
        if connect_to:
            # Pega o peso digitado de forma segura (se for vazio, vira '0')
            w = str(weight).strip() if weight is not None and str(weight).strip() != "" else '0'
            
            # --- NOVA TRAVA: Avisa se tentar por peso num grafo Não Ponderado ---
            if not props['is_weighted'] and w != '0':
                 return new_style, node_id, connect_to, weight, "⚠️ O grafo atual é Não Ponderado. Altere para 'Ponderado' no menu Ações primeiro.", dash.no_update, dash.no_update

            base_class = (' undirected' if not props['is_directed'] else '')
            if not props['is_weighted']:
                base_class += ' unweighted'
                w = '0' 
            
            new_elements.append({'data': {'id': f'e_{node_id}_{connect_to}', 'source': node_id, 'target': connect_to, 'weight': w}, 'classes': base_class})
            
            if not props['is_directed'] and node_id != connect_to:
                new_elements.append({'data': {'id': f'e_{connect_to}_{node_id}_auto', 'source': connect_to, 'target': node_id, 'weight': w, 'is_auto_reverse': True}, 'classes': base_class})

        new_style['display'] = 'none'
        new_counter = counter + 1 if node_id == str(counter) else counter

        return new_style, "", None, "", "", new_elements, new_counter
        
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# ==========================================
# LÓGICA PARA CARREGAR GRAFOS PRONTOS (TEMPLATES)
# ==========================================
@app.callback(
    Output('cyto-graph', 'elements', allow_duplicate=True),
    Output('node-counter', 'data', allow_duplicate=True),
    Output('graph-props', 'data', allow_duplicate=True),
    Output('btn-orientado', 'style', allow_duplicate=True),
    Output('btn-ponderado', 'style', allow_duplicate=True),
    Input('btn-grafo-casa', 'n_clicks'),
    Input('btn-grafo-circulo', 'n_clicks'),
    Input('btn-grafo-arvore', 'n_clicks'),
    State('anim-steps', 'data'),
    prevent_initial_call=True
)
def carregar_grafos_prontos(n_casa, n_circ, n_arv, anim_steps):
    trigger = ctx.triggered_id
    if anim_steps and len(anim_steps) > 0: raise PreventUpdate

    style_ativo = {**DROPDOWN_ITEM_STYLE, 'backgroundColor': '#444'}
    style_inativo = {**DROPDOWN_ITEM_STYLE, 'backgroundColor': '#2980b9'}

    # --- CASA (5V, Não Orientado, Sem Peso -> Peso 0) ---
    if trigger == 'btn-grafo-casa':
        props = {'is_directed': False, 'is_weighted': False}
        el = [
            {'data': {'id': '1', 'label': '1'}, 'position': {'x': 400, 'y': 100}},
            {'data': {'id': '2', 'label': '2'}, 'position': {'x': 300, 'y': 250}},
            {'data': {'id': '3', 'label': '3'}, 'position': {'x': 500, 'y': 250}},
            {'data': {'id': '4', 'label': '4'}, 'position': {'x': 300, 'y': 450}},
            {'data': {'id': '5', 'label': '5'}, 'position': {'x': 500, 'y': 450}},
        ]
        conexoes = [('1','2'), ('1','3'), ('2','3'), ('2','4'), ('3','5'), ('4','5')]
        for u, v in conexoes:
            el.append({'data': {'id': f'e_{u}_{v}', 'source': u, 'target': v, 'weight': '0'}, 'classes': ' undirected unweighted'})
            el.append({'data': {'id': f'e_{v}_{u}_auto', 'source': v, 'target': u, 'weight': '0', 'is_auto_reverse': True}, 'classes': ' undirected unweighted'})
        return el, 6, props, style_inativo, style_inativo

    # --- CÍRCULO (8V, Orientado, Sem Peso -> Peso 0) ---
    elif trigger == 'btn-grafo-circulo':
        props = {'is_directed': True, 'is_weighted': False}
        el = []
        for i in range(8):
            angle = (2 * math.pi * i) / 8
            x, y = 400 + 200 * math.cos(angle), 300 + 200 * math.sin(angle)
            el.append({'data': {'id': str(i+1), 'label': str(i+1)}, 'position': {'x': x, 'y': y}})
        for i in range(8):
            u, v = str(i+1), str(((i + 1) % 8) + 1)
            el.append({'data': {'id': f'e_{u}_{v}', 'source': u, 'target': v, 'weight': '0'}, 'classes': ' unweighted'})
        return el, 9, props, style_ativo, style_inativo

    # --- ÁRVORE (15V, Orientado, Sem Peso -> Peso 0) ---
    elif trigger == 'btn-grafo-arvore':
        props = {'is_directed': True, 'is_weighted': False}
        el = []
        for i in range(1, 16):
            camada = int(math.log2(i))
            pos_na_camada = i - (2**camada)
            espacamento = 800 / (2**camada)
            x = (pos_na_camada * espacamento) + (espacamento / 2)
            y = (camada * 120) + 100
            el.append({'data': {'id': str(i), 'label': str(i)}, 'position': {'x': x, 'y': y}})
        for i in range(1, 8):
            for v in [2*i, 2*i + 1]:
                el.append({'data': {'id': f'e_{i}_{v}', 'source': str(i), 'target': str(v), 'weight': '0'}, 'classes': ' unweighted'})
        return el, 16, props, style_ativo, style_inativo

    raise PreventUpdate

# ==========================================
# 1. ABRIR E FECHAR A JANELA DO GRAFO PERSONALIZADO
# ==========================================
@app.callback(
    Output('custom-graph-modal', 'style'),
    Input('btn-grafo-custom-trigger', 'n_clicks'),
    Input('btn-cancel-custom', 'n_clicks'),
    Input('btn-confirm-custom', 'n_clicks'),
    State('custom-graph-modal', 'style'),
    prevent_initial_call=True
)
def toggle_custom_modal(abrir, cancelar, confirmar, style):
    trigger = ctx.triggered_id
    new_style = style.copy() if style else {}
    if trigger == 'btn-grafo-custom-trigger':
        new_style['display'] = 'flex'
    else:
        new_style['display'] = 'none'
    return new_style

# ==========================================
# 2. GERAR O GRAFO COMPLETO
# ==========================================
@app.callback(
    Output('cyto-graph', 'elements', allow_duplicate=True),
    Output('node-counter', 'data', allow_duplicate=True),
    Output('graph-props', 'data', allow_duplicate=True),
    Output('btn-orientado', 'style', allow_duplicate=True),
    Output('btn-ponderado', 'style', allow_duplicate=True),
    Input('btn-confirm-custom', 'n_clicks'),
    State('custom-graph-input', 'value'),
    State('anim-steps', 'data'),
    prevent_initial_call=True
)
def gerar_grafo_personalizado(n_clicks, qtd, anim_steps):
    if anim_steps and len(anim_steps) > 0: raise PreventUpdate
    if not n_clicks or not qtd or qtd < 1: raise PreventUpdate

    props = {'is_directed': False, 'is_weighted': False}
    style_ativo = {**DROPDOWN_ITEM_STYLE, 'backgroundColor': '#444'}
    style_inativo = {**DROPDOWN_ITEM_STYLE, 'backgroundColor': '#2980b9'}

    el = []
    raio = max(250, qtd * 12) 
    
    for i in range(qtd):
        angle = (2 * math.pi * i) / qtd
        x = 400 + raio * math.cos(angle)
        y = 300 + raio * math.sin(angle)
        el.append({'data': {'id': str(i+1), 'label': str(i+1)}, 'position': {'x': x, 'y': y}})

    for i in range(1, qtd + 1):
        for j in range(i + 1, qtd + 1):
            u, v = str(i), str(j)
            el.append({'data': {'id': f'e_{u}_{v}', 'source': u, 'target': v, 'weight': '0'}, 'classes': ' undirected unweighted'})
            el.append({'data': {'id': f'e_{v}_{u}_auto', 'source': v, 'target': u, 'weight': '0', 'is_auto_reverse': True}, 'classes': ' undirected unweighted'})

    return el, qtd + 1, props, style_inativo, style_inativo

# ==========================================
# NOVO: ATUALIZAR O TEXTO DO ZOOM EM TEMPO REAL
# ==========================================
@app.callback(
    Output('zoom-label', 'children'),
    Input('zoom-slider', 'value')
)
def atualizar_texto_zoom(valor):
    return f"Ajuste de Zoom: {valor:.2f}x"

# ==========================================
# 3. ALTERNADOR DE TEMA (MODO CLARO E ESCURO)
# ==========================================
@app.callback(
    Output('app-wrapper', 'className'),
    Output('cyto-graph', 'stylesheet'),
    Output('zoom-slider', 'marks'),
    Output('zoom-label', 'style'),
    Input('btn-theme-toggle', 'n_clicks'),
    State('cyto-graph', 'stylesheet'),
    prevent_initial_call=True
)
def alternar_tema(n_clicks, current_style):
    if not current_style:
        from config import STYLESHEET
        current_style = copy.deepcopy(STYLESHEET)
    else:
        current_style = copy.deepcopy(current_style)

    is_dark = n_clicks and n_clicks % 2 != 0

    for rule in current_style:
        if rule.get('selector') == 'edge':
            if is_dark:
                rule['style']['text-background-opacity'] = 0  
                rule['style']['color'] = '#ffffff'            
                rule['style']['text-outline-width'] = 3
                rule['style']['text-outline-color'] = '#121212' 
            else:
                rule['style']['text-background-opacity'] = 1  
                rule['style']['color'] = '#c0392b'            
                rule['style']['text-outline-width'] = 0
                
    theme_class = 'dark-theme' if is_dark else 'light-theme'
    cor_texto = '#ffffff' if is_dark else '#2c3e50'
    
    novas_marcas = {
        0.15: {'label': '0.15x', 'style': {'color': cor_texto}},
        1: {'label': '1x', 'style': {'color': cor_texto}},
        2.5: {'label': '2.5x', 'style': {'color': cor_texto}}
    }
    estilo_label = {'fontWeight': 'bold', 'color': cor_texto, 'fontSize': '14px', 'marginBottom': '5px', 'display': 'block'}
    
    return theme_class, current_style, novas_marcas, estilo_label

if __name__ == '__main__':
    app.run(debug=True, dev_tools_ui=False, dev_tools_props_check=False)
