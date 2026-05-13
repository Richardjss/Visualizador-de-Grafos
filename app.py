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
import time

from layout import create_layout
from config import *

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.layout = create_layout()

app.clientside_callback(
    dash.ClientsideFunction(namespace='clientside', function_name='setup_interactions'),
    Output('hidden-v-btn', 'id'),
    Input('cyto-graph', 'id')
)

@app.callback(
    Output("menu-acoes", "style"), Output("menu-arquivo", "style"), Output("menu-grafos", "style"), Output("menu-algoritmos", "style"),
    Output("top-menu-overlay", "style"),
    Input("upload-grafo", "contents"), Input("btn-confirm-save", "n_clicks"),
    Input("btn-toggle-acoes", "n_clicks"), Input("btn-toggle-arquivo", "n_clicks"), 
    Input("btn-toggle-grafos", "n_clicks"), Input("btn-toggle-algoritmos", "n_clicks"),
    Input('btn-confirm-bfs', 'n_clicks'), Input('btn-confirm-dfs', 'n_clicks'),
    Input('top-menu-overlay', 'n_clicks'),
    Input('btn-grafo-custom-trigger', 'n_clicks'),
    Input("btn-floyd", "n_clicks"),
    State("menu-acoes", "style"), State("menu-arquivo", "style"), State("menu-grafos", "style"), State("menu-algoritmos", "style"),
    State('anim-steps', 'data'),
    prevent_initial_call=True
)
def toggle_top_menus(upload_trigger, save_trigger, n_ac, n_ar, n_gr, n_al, bfs_ok, dfs_ok, click_overlay, btn_custom, btn_floyd, st_ac, st_ar, st_gr, st_al, anim_steps):
    
    trigger = ctx.triggered_id 
    
    s_ac = st_ac.copy() if st_ac else {}
    s_ar = st_ar.copy() if st_ar else {}
    s_gr = st_gr.copy() if st_gr else {}
    s_al = st_al.copy() if st_al else {}
    
    overlay_off = {'display': 'none'}
    overlay_on = {'display': 'block', 'position': 'fixed', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 'zIndex': 900, 'backgroundColor': 'transparent'}

    if trigger in ['upload-grafo', 'btn-confirm-save', 'top-menu-overlay', 'btn-confirm-bfs', 'btn-confirm-dfs', 'btn-grafo-custom-trigger', 'btn-floyd']:
        s_ac['display'] = s_ar['display'] = s_gr['display'] = s_al['display'] = 'none'
        return s_ac, s_ar, s_gr, s_al, overlay_off

    if anim_steps and len(anim_steps) > 0:
        raise PreventUpdate

    if trigger == 'btn-toggle-acoes':
        target = 'flex' if s_ac.get('display', 'none') == 'none' else 'none'
        s_ac['display'], s_ar['display'], s_gr['display'], s_al['display'] = target, 'none', 'none', 'none'
    elif trigger == 'btn-toggle-arquivo':
        target = 'flex' if s_ar.get('display', 'none') == 'none' else 'none'
        s_ac['display'], s_ar['display'], s_gr['display'], s_al['display'] = 'none', target, 'none', 'none'
    elif trigger == 'btn-toggle-grafos':
        target = 'flex' if s_gr.get('display', 'none') == 'none' else 'none'
        s_ac['display'], s_ar['display'], s_gr['display'], s_al['display'] = 'none', 'none', target, 'none'
    elif trigger == 'btn-toggle-algoritmos':
        target = 'flex' if s_al.get('display', 'none') == 'none' else 'none'
        s_ac['display'], s_ar['display'], s_gr['display'], s_al['display'] = 'none', 'none', 'none', target

    final_overlay = overlay_on if any(s.get('display') == 'flex' for s in [s_ac, s_ar, s_gr, s_al]) else overlay_off
    return s_ac, s_ar, s_gr, s_al, final_overlay

# --- LÓGICA DA JANELA MODAL DE SALVAR ---
@app.callback(
    Output('save-modal', 'style'),
    Input('btn-salvar-modal-trigger', 'n_clicks'),
    Input('hidden-ctrl-s-btn', 'n_clicks'),
    Input('btn-cancel-save', 'n_clicks'),
    Input('btn-confirm-save', 'n_clicks'),
    State('save-modal', 'style'),
    State('anim-steps', 'data'),
    prevent_initial_call=True
)
def toggle_save_modal(n_salvar, n_ctrl_s, n_cancel, n_confirm, style, anim_steps):
    trigger = ctx.triggered_id
    
    if trigger == 'hidden-ctrl-s-btn' and anim_steps and len(anim_steps) > 0:
        raise PreventUpdate

    new_style = style.copy() if style else {}
    if trigger in ['btn-salvar-modal-trigger', 'hidden-ctrl-s-btn']:
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
    edges = [el for el in elements if 'source' in el['data']]
    
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
    
    if total > 1:
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
    
    Input('hidden-v-btn', 'n_clicks'), Input('hidden-e-btn', 'n_clicks'), 
    Input('hidden-right-click-btn', 'n_clicks'), Input('hidden-dbl-click-btn', 'n_clicks'),
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
def master_controller(v_clicks, e_clicks, rc_clicks, dbl_clicks, tap_node, btn_node, btn_edge, btn_rename, btn_del, btn_close, 
                      btn_ren_edge, btn_del_edge, btn_close_edge, 
                      overlay_click, btn_save, btn_cancel, btn_orientado_clicks, btn_ponderado_clicks, 
                      upload_contents, btn_limpar, btn_details, btn_multi_del,
                      rc_data, dbl_data, edit_val, elements, counter, state, selected, orient_style, pond_style, props, anim_steps,
                      sel_nodes, sel_edges):
    
    trigger = ctx.triggered_id

    # Ignora ações se a animação estiver rodando
    if anim_steps and len(anim_steps) > 0:
        if trigger in ['hidden-right-click-btn', 'hidden-dbl-click-btn', 'hidden-v-btn', 'hidden-e-btn', 'cyto-graph', 'btn-delete-multi']:
            return [dash.no_update] * 15

    hide_node_menu, hide_edge_menu, hide_overlay = {'display': 'none'}, {'display': 'none'}, {'display': 'none'}
    show_overlay = {'display': 'block', 'position': 'fixed', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 'zIndex': 999, 'cursor': 'default'}
    hide_status, hide_modal = {'display': 'none'}, {'display': 'none'}
    show_status = {'position': 'absolute', 'top': '10px', 'left': '50%', 'transform': 'translateX(-50%)', 'backgroundColor': '#2980b9', 'color': 'white', 'padding': '10px 20px', 'borderRadius': '20px', 'zIndex': 1000, 'fontWeight': 'bold', 'display': 'block'}

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

    elif trigger == 'btn-limpar':
        
        return [], 1, {'mode': 'idle', 'source_node': None}, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", style_ativo, style_ativo, props_padrao, None

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
            
            # --- 1. VALIDAÇÃO DE FORMATO (CABEÇALHO) ---
            try:
                header = lines[0].split()

                if len(header) != 2: raise ValueError
                v_esperados = int(header[0])
                e_esperados = int(header[1])
            except (IndexError, ValueError):
                msg = [
                    "⚠️ Formato de arquivo inválido! O cabeçalho deve ter apenas: Vértices Arestas.", 
                    html.Span(time.time(), style={'display': 'none'})
                ]
                return dash.no_update, dash.no_update, dash.no_update, hide_node_menu, hide_edge_menu, hide_overlay, None, msg, {**show_status, 'backgroundColor': '#c0392b'}, hide_modal, "", dash.no_update, dash.no_update, dash.no_update, None
            
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
                    if "Orientado:" in line: 
                        val = line.split(":", 1)[-1].strip().lower()
                        new_props['is_directed'] = (val != 'false')
                    elif "Ponderado:" in line: 
                        val = line.split(":", 1)[-1].strip().lower()
                        new_props['is_weighted'] = (val != 'false')
                    elif len(parts) >= 3: 
                        pos[parts[0]] = (float(parts[1]), float(parts[2]))

            # Coleta IDs únicos de nós para contagem
            all_node_ids = set()
            for e in temp_edges:
                all_node_ids.add(e[0])
                if len(e) >= 2: all_node_ids.add(e[1])
            all_node_ids.update(pos.keys())
            
            # --- 2. VERIFICAÇÃO RIGOROSA DE CONTAGEM ---
            arestas_validas = [e for e in temp_edges if len(e) >= 2]
            v_encontrados = len(all_node_ids)
            e_encontrados = len(arestas_validas)
            
            if v_encontrados != v_esperados or e_encontrados != e_esperados:
                msg = [
                    f"❌ Erro de Contagem: O arquivo indica {v_esperados}V/{e_esperados}E, mas encontrei {v_encontrados}V/{e_encontrados}E.", 
                    html.Span(time.time(), style={'display': 'none'})
                ]
                return dash.no_update, dash.no_update, dash.no_update, hide_node_menu, hide_edge_menu, hide_overlay, None, msg, {**show_status, 'backgroundColor': '#c0392b'}, hide_modal, "", dash.no_update, dash.no_update, dash.no_update, None
            
            new_elements, max_id = [], 1
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
            
            base_class = (' undirected' if not new_props['is_directed'] else '') + (' unweighted' if not new_props['is_weighted'] else '')
            
            # Memória para evitar duplicatas em grafos não orientados
            vistos_nao_orientados = set()

            for e in temp_edges:
                if len(e) < 2: continue
                u, v = e[0], e[1]
                w = e[2] if len(e) >= 3 and new_props['is_weighted'] else '0'
                
                if not new_props['is_directed']:
                    par = tuple(sorted([u, v]))
                    if par in vistos_nao_orientados: continue
                    vistos_nao_orientados.add(par)
                
                new_elements.append({'data': {'id': f'e_{u}_{v}', 'source': u, 'target': v, 'weight': w}, 'classes': base_class})
            
            novo_orient_style = {**DROPDOWN_ITEM_STYLE, 'backgroundColor': '#444' if new_props['is_directed'] else '#2980b9'}
            novo_pond_style = {**DROPDOWN_ITEM_STYLE, 'backgroundColor': '#444' if new_props['is_weighted'] else '#2980b9'}

            return new_elements, max_id, {'mode': 'idle', 'source_node': None}, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", novo_orient_style, novo_pond_style, new_props, None
        
        except Exception as e:
            print("Erro ao ler ficheiro:", e)
            raise PreventUpdate
        
    elif trigger == 'btn-orientado':
        props['is_directed'] = not props['is_directed']
        new_elements = []
        
        if not props['is_directed']:
            orient_style['backgroundColor'] = '#2980b9' 
            vistos = set()
            for el in elements:
                if 'source' in el['data']:
                    u, v = el['data']['source'], el['data']['target']
                    par = tuple(sorted([u, v]))
                    
                    if par not in vistos:
                        vistos.add(par)
                        el_copy = copy.deepcopy(el)
                        if 'undirected' not in el_copy.get('classes', ''):
                            el_copy['classes'] = el_copy.get('classes', '') + ' undirected'
                        new_elements.append(el_copy)
                else:
                    new_elements.append(copy.deepcopy(el))
        else:
            orient_style['backgroundColor'] = '#444'
            for el in elements:
                el_copy = copy.deepcopy(el)
                if 'source' in el_copy['data']: 
                    el_copy['classes'] = el_copy.get('classes', '').replace(' undirected', '')
                new_elements.append(el_copy)
                
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
        
        if data.get('bg_cancel'):
            if state.get('mode') == 'adding_edge':
                return elements, counter, {'mode': 'idle', 'source_node': None}, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update
            raise PreventUpdate
            
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
                            novo_peso = str(int(val)) if val.is_integer() else str(val)
                            el['data']['weight'] = novo_peso
                            
                            if not props['is_weighted'] and novo_peso != '0':
                                props['is_weighted'] = True
                                pond_style = {**DROPDOWN_ITEM_STYLE, 'backgroundColor': '#444'}
                                
                                for e in new_elements:
                                    if 'source' in e['data']:
                                        e['classes'] = e.get('classes', '').replace(' unweighted', '')
                                        
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
            
            exists = False
            for e in new_elements:
                if 'source' in e['data']:
                    if props['is_directed']:
                        if e['data']['source'] == source and e['data']['target'] == node_id:
                            exists = True; break
                    else:
                        if (e['data']['source'] == source and e['data']['target'] == node_id) or \
                           (e['data']['source'] == node_id and e['data']['target'] == source):
                            exists = True; break
                            
            if not exists:
                base_class = (' undirected' if not props['is_directed'] else '') + (' unweighted' if not props['is_weighted'] else '')
                new_elements.append({'data': {'id': f'e_{source}_{node_id}', 'source': source, 'target': node_id, 'weight': '0'}, 'classes': base_class})

            return new_elements, counter, {'mode': 'idle', 'source_node': None}, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update
        
    elif trigger == 'btn-add-node' and selected:
        parent_pos = next((el['position'] for el in elements if el['data']['id'] == selected), {'x': 400, 'y': 300})
        elements.append({'data': {'id': str(counter), 'label': str(counter)}, 'position': {'x': parent_pos['x'], 'y': parent_pos['y'] + 80}})
        return elements, counter + 1, state, hide_node_menu, hide_edge_menu, hide_overlay, None, "", hide_status, hide_modal, "", orient_style, pond_style, props, dash.no_update

    elif trigger in ['btn-add-edge', 'hidden-e-btn']:
        alvo = selected
        if trigger == 'hidden-e-btn' and sel_nodes:
            alvo = sel_nodes[0]['id']
            
        if alvo:
            return elements, counter, {'mode': 'adding_edge', 'source_node': alvo}, hide_node_menu, hide_edge_menu, hide_overlay, None, "Clique no destino...", show_status, hide_modal, "", orient_style, pond_style, props, dash.no_update
        
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
    Input('btn-confirm-bfs', 'n_clicks'), Input('btn-confirm-dfs', 'n_clicks'),
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
    edges = [el for el in elements if 'source' in el['data']]
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
    
    edges = [el for el in elements if 'source' in el['data']]
    
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

def algoritmo_floyd(elements, props):
    # Pega todos os vértices e os ordena de forma inteligente (1, 2, 3...)
    nodes = [el['data']['id'] for el in elements if 'source' not in el['data']]
    try: nodes.sort(key=lambda x: int(x))
    except ValueError: nodes.sort()
    
    n = len(nodes)
    node_to_idx = {node_id: i for i, node_id in enumerate(nodes)}
    
    # Cria a matriz inicial com infinito e 0 na diagonal
    dist = [[float('inf')] * n for _ in range(n)]
    next_node = [[None] * n for _ in range(n)]
    
    for i in range(n): dist[i][i] = 0
    
    # Preenche a matriz com as estradas diretas que existem
    for el in elements:
        if 'source' in el['data']:
            u, v = el['data']['source'], el['data']['target']
            w = float(el['data'].get('weight', 0)) if props['is_weighted'] else 1.0
            i, j = node_to_idx[u], node_to_idx[v]
            if w < dist[i][j]:
                dist[i][j] = w
                next_node[i][j] = v
            if not props['is_directed']:
                if w < dist[j][i]:
                    dist[j][i] = w
                    next_node[j][i] = u

    steps = []
    steps.append({'matrix': copy.deepcopy(dist), 'pivot': None, 'i': None, 'j': None, 'desc': "Matriz Inicial", 'nodes_list': nodes})

    # O algoritmo (os 3 laços de repetição)
    for k in range(n):
        for i in range(n):
            for j in range(n):

                # Pula os frames redundantes onde os nós se sobrepõem na animação
                if i == k or j == k:
                    continue

                # Evita somar com infinito
                if dist[i][k] != float('inf') and dist[k][j] != float('inf'):
                    
                    novo_custo = dist[i][k] + dist[k][j]
                    
                    # Condição de relaxamento (melhoria)
                    if dist[i][j] > novo_custo:
                        valor_antigo = dist[i][j]
                        
                        dist[i][j] = novo_custo
                        next_node[i][j] = next_node[i][k]
                        
                        str_antigo = "∞" if valor_antigo == float('inf') else f"{valor_antigo:.1f}"
                        str_novo = f"{novo_custo:.1f}"
                        
                        # Usa a variável 'nodes' para pegar o nome real do vértice
                        mensagem_balao = f"Melhoria! {nodes[i]} → {nodes[k]} → {nodes[j]} custa {str_novo} (antes era {str_antigo})"
                        
                        # Salva o frame com as chaves corretas que o front-end espera
                        steps.append({
                            'matrix': copy.deepcopy(dist),
                            'pivot': nodes[k],
                            'i': nodes[i],
                            'j': nodes[j],
                            'desc': mensagem_balao,
                            'nodes_list': nodes
                        })
                    else:
                        # Captura os valores para explicar o motivo de ter sido descartado
                        valor_antigo = dist[i][j]
                        str_antigo = "∞" if valor_antigo == float('inf') else f"{valor_antigo:.1f}"
                        str_novo = f"{novo_custo:.1f}"
                        
                        mensagem_balao = f"Testando {nodes[i]} → {nodes[k]} → {nodes[j]} custa {str_novo} (Mantém o {str_antigo})"
                        
                        # Salva o frame avisando que testou, mas não houve melhoria
                        steps.append({
                            'matrix': copy.deepcopy(dist),
                            'pivot': nodes[k],
                            'i': nodes[i],
                            'j': nodes[j],
                            'desc': mensagem_balao,
                            'nodes_list': nodes
                        })
                        
    # No último passo, envia a matriz next_node para podermos usar na busca de caminho
    steps.append({'matrix': dist, 'next_node': next_node, 'pivot': None, 'i': None, 'j': None, 'desc': "✅ Floyd-Warshall Concluído!", 'nodes_list': nodes})
    
    return steps

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
    Input('btn-floyd', 'n_clicks'),
    State('bfs-start-node', 'value'),
    State('dfs-start-node', 'value'),
    State('cyto-graph', 'elements'),
    State('graph-props', 'data'),
    prevent_initial_call=True
)
def gerar_roteiro_animacao(bfs_click, dfs_click, floyd_click, bfs_start, dfs_start, elements, props):
    trigger = ctx.triggered_id
    
    if trigger == 'btn-floyd':
        steps = algoritmo_floyd(elements, props)
        overlay_style = {'display': 'block', 'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '70px', 'zIndex': 1500, 'backgroundColor': 'transparent', 'cursor': 'not-allowed'}
        return steps, 0, False, overlay_style
    
    start_node = bfs_start if trigger == 'btn-confirm-bfs' else dfs_start
    if not start_node or not elements: raise PreventUpdate

    start_node = str(start_node).strip()
    exists = any(el['data']['id'] == start_node for el in elements if 'source' not in el['data'])
    if not exists:
        raise PreventUpdate

    # --- LÓGICA DA MATRIZ DE ADJACÊNCIA ---
    is_dir = props.get('is_directed', True)
    adj_list = {el['data']['id']: [] for el in elements if 'source' not in el['data']}
    
    for el in elements:
        if 'source' in el['data']:
            u, v = el['data']['source'], el['data']['target']
            eid = el['data']['id'] # Salva o ID da linha
            adj_list[u].append((v, eid)) # Guarda uma tupla (Destino, Linha_Usada)
            if not is_dir and u != v:
                adj_list[v].append((u, eid))
                
    for u in adj_list:
        try: adj_list[u].sort(key=lambda x: int(x[0]))
        except ValueError: adj_list[u].sort(key=lambda x: x[0])

    steps, visited, tree_edges = [], [], []
    
    if trigger == 'btn-confirm-bfs':
        fila = [(start_node, None)]
        enqueued = {start_node}
        steps.append({'current': None, 'visited': [], 'frontier': [start_node], 'ordem': [], 'tree_edges': []})
        
        while fila:
            current, edge_used = fila.pop(0)
            if edge_used: tree_edges.append(edge_used)
            
            frontier_display = [item[0] for item in fila]
            steps.append({'current': current, 'visited': list(visited), 'frontier': frontier_display, 'ordem': list(visited), 'tree_edges': list(tree_edges)})
            
            for vizinho, eid in adj_list.get(current, []):
                if vizinho not in enqueued:
                    enqueued.add(vizinho)
                    fila.append((vizinho, eid))
                    
            frontier_display = [item[0] for item in fila]
            steps.append({'current': current, 'visited': list(visited), 'frontier': frontier_display, 'ordem': list(visited), 'tree_edges': list(tree_edges)})
            visited.append(current)
            
    elif trigger == 'btn-confirm-dfs':
        pilha = [(start_node, None)]
        steps.append({'current': None, 'visited': [], 'frontier': [start_node], 'ordem': [], 'tree_edges': []})
        
        while pilha:
            current, edge_used = pilha.pop()
            if current not in visited:
                if edge_used: tree_edges.append(edge_used)
                
                frontier_display = [item[0] for item in pilha]
                steps.append({'current': current, 'visited': list(visited), 'frontier': frontier_display, 'ordem': list(visited), 'tree_edges': list(tree_edges)})
                
                for vizinho, eid in reversed(adj_list.get(current, [])):
                    if vizinho not in visited:
                        pilha.append((vizinho, eid))
                        
                frontier_display = [item[0] for item in pilha]
                steps.append({'current': current, 'visited': list(visited), 'frontier': frontier_display, 'ordem': list(visited), 'tree_edges': list(tree_edges)})
                visited.append(current)

    steps.append({'current': None, 'visited': list(visited), 'frontier': [], 'ordem': list(visited), 'tree_edges': list(tree_edges)})

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
    Output('legend-panel', 'style', allow_duplicate=True),
    Output('legend-panel', 'children'),
    Input('anim-index', 'data'),
    State('anim-steps', 'data'),
    State('cyto-graph', 'elements'),
    prevent_initial_call=True
)
def renderizar_animacao(idx, steps, elements):
    if not steps: raise PreventUpdate
    step_data = steps[idx]
    is_end = (idx == len(steps) - 1)
    
    new_elements = copy.deepcopy(elements)
    
    # === SE FOR O FLOYD-WARSHALL ===
    if 'matrix' in step_data:
        matrix, pivot, u, v = step_data['matrix'], step_data.get('pivot'), step_data.get('i'), step_data.get('j')
        nodes_list = step_data['nodes_list']
        
        # Pinta o Grafo
        for el in new_elements:
            base = el.get('classes', '').replace(' visited', '').replace(' frontier', '').replace(' current', '').replace(' tree-edge', '')
            base = base.replace(' floyd-pivot', '').replace(' floyd-source', '').replace(' floyd-target', '')
            el['classes'] = base
            
            if 'source' not in el['data']:
                nid = el['data']['id']
                if nid == pivot: el['classes'] += ' floyd-pivot'
                elif nid == u: el['classes'] += ' floyd-source'
                elif nid == v: el['classes'] += ' floyd-target'

        # --- CABEÇALHO DA TABELA (Travando a 1ª Coluna) ---
        thead = html.Thead(html.Tr(
            [html.Th(r"De \ Para", className='floyd-th')] + 
            [html.Th(n, className='floyd-th') for n in nodes_list]
        ))
        
        # --- CORPO DA TABELA ---
        linhas_tabela = []
        for r_idx, row in enumerate(matrix):
            celulas = [html.Td(html.B(nodes_list[r_idx]), className='floyd-td-header')]
            
            for c_idx, val in enumerate(row):
                str_val = "∞" if val is None or val == float('inf') else ("0" if val == 0 and type(val) in (int, float) and float(val).is_integer() else str(val).replace('.0',''))
                
                # Identifica qual célula estamos
                classe_celula = 'floyd-td'
                if nodes_list[r_idx] == u and nodes_list[c_idx] == v:
                    classe_celula += ' floyd-cell-active' # Interseção
                elif nodes_list[r_idx] == u:
                    classe_celula += ' floyd-highlight-row' # Linha Atual
                elif nodes_list[c_idx] == v:
                    classe_celula += ' floyd-highlight-col' # Coluna Atual
                    
                celulas.append(html.Td(str_val, className=classe_celula))
            linhas_tabela.append(html.Tr(celulas))
            
        tabela_html = html.Table([thead, html.Tbody(linhas_tabela)], className='floyd-matrix-table')
        status_msg = step_data['desc']
    
        sidebar_content = [
            html.H3("Matriz de Distâncias", style={'marginTop': '15px', 'borderBottom': '2px solid #9b59b6', 'paddingBottom': '10px', 'paddingRight': '60px', 'textAlign': 'center', 'flexShrink': '0'}),
            html.Div(tabela_html, style={'overflow': 'auto', 'flex': '1 1 auto', 'minHeight': '0', 'marginTop': '5px'})
        ]

    # === SE FOR BFS / DFS ===
    else:
        current, visited, frontier, ordem = step_data.get('current'), step_data.get('visited', []), step_data.get('frontier', []), step_data.get('ordem', [])
        tree_edges = step_data.get('tree_edges', [])
        
        for el in new_elements:
            base = el.get('classes', '').replace(' visited', '').replace(' frontier', '').replace(' current', '').replace(' tree-edge', '')
            el['classes'] = base
            if 'source' not in el['data']:
                nid = el['data']['id']
                if nid == current: el['classes'] += ' current'
                elif nid in visited: el['classes'] += ' visited'
                elif nid in frontier: el['classes'] += ' frontier'
            else:
                if el['data']['id'] in tree_edges: el['classes'] += ' tree-edge'

        status_msg = f"Analisando: {current} | Caminho: {' ➔ '.join(ordem)}" if current else f"Caminho: {' ➔ '.join(ordem)}"
        if is_end: status_msg = f"✅ Concluído! Ordem final: {' ➔ '.join(ordem)}"
        
        def badge(texto, cor): return html.Span(texto, style={'backgroundColor': cor, 'color': 'white', 'padding': '4px 10px', 'borderRadius': '12px', 'marginRight': '5px', 'marginBottom': '5px', 'display': 'inline-block', 'fontWeight': 'bold', 'fontSize': '14px'})
        
        sidebar_content = [
            html.H3("Trace (Memória)", style={'marginTop': '0', 'color': '#2c3e50', 'borderBottom': '2px solid #3498db', 'paddingBottom': '10px', 'textAlign': 'center'}),
            html.Div([html.B("📌 Vértice Atual:", style={'display': 'block', 'marginBottom': '5px'}), badge(current, '#e74c3c') if current else html.Span("Nenhum")], style={'marginBottom': '20px'}),
            html.Div([html.B("⏳ Fila / Pilha:", style={'display': 'block', 'marginBottom': '5px'}), html.Div([badge(v, '#f39c12') for v in frontier] if frontier else [html.Span("Vazia")])], style={'marginBottom': '20px', 'borderLeft': '3px solid #f39c12', 'paddingLeft': '10px'}),
            html.Div([html.B("✅ Visitados:", style={'display': 'block', 'marginBottom': '5px'}), html.Div([badge(v, '#27ae60') for v in visited] if visited else [html.Span("Nenhum")])], style={'borderLeft': '3px solid #27ae60', 'paddingLeft': '10px'})
        ]

    # === ESTILOS GERAIS PARA AMBOS ===
    status_style = {'position': 'absolute', 'top': '15px', 'left': '50%', 'transform': 'translateX(-50%)', 'backgroundColor': '#27ae60' if is_end else '#34495e', 'color': 'white', 'padding': '12px 25px', 'borderRadius': '30px', 'zIndex': 4000, 'fontWeight': 'bold', 'display': 'block', 'boxShadow': '0 4px 10px rgba(0,0,0,0.3)'}
    player_style = {'display': 'flex', 'position': 'absolute', 'bottom': '20px', 'left': '50%', 'transform': 'translateX(-50%)', 'backgroundColor': '#111', 'padding': '10px 25px', 'borderRadius': '30px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.6)', 'zIndex': 2000, 'alignItems': 'center', 'gap': '20px'}
    close_btn_style = {'display': 'flex', 'position': 'absolute', 'top': '70px', 'left': '50%', 'transform': 'translateX(-50%)', 'backgroundColor': 'white', 'color': '#e74c3c', 'border': '2px solid #e74c3c', 'borderRadius': '50%', 'width': '35px', 'height': '35px', 'fontSize': '18px', 'cursor': 'pointer', 'zIndex': 4000, 'alignItems': 'center', 'justifyContent': 'center', 'fontWeight': 'bold'}
    
    sidebar_style = {
        'display': 'flex', 'flexDirection': 'column', 'position': 'absolute', 'top': '15px', 'right': '15px', 
        'backgroundColor': 'rgba(255, 255, 255, 0.95)', 'padding': '20px', 
        'borderRadius': '8px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.4)', 
        'zIndex': 2000, 'border': '1px solid #bdc3c7', 'overflow': 'hidden',
        'maxHeight': 'calc(100vh - 140px)'
    }

    if is_end and 'matrix' in step_data:
        sidebar_content.append(html.Hr(style={'margin': '10px 0', 'flexShrink': '0'}))
        sidebar_content.append(html.Div([
            html.B("🔍 Testar Caminho Curto:"),
            html.Div([
                dbc.Input(id='path-start', placeholder="De", style={'width': '45%', 'display': 'inline-block'}),
                dbc.Input(id='path-end', placeholder="Para", style={'width': '45%', 'display': 'inline-block', 'marginLeft': '5%'})
            ], style={'marginTop': '10px'}),
            html.Button("Ver Caminho", id='btn-test-path', className='hover-btn', 
                        style={'width': '100%', 'marginTop': '10px', 'backgroundColor': '#9c3edc', 'color': 'white', 'border': 'none', 'padding': '8px', 'borderRadius': '4px', 'fontWeight': 'bold'}),
            html.Div(id='path-result', style={'marginTop': '10px', 'textAlign': 'center', 'fontWeight': 'bold'})
        ], style={'flexShrink': '0'}))
    
    legend_style = {
        'display': 'block', 'position': 'absolute', 'top': '15px', 'left': '15px',
        'backgroundColor': 'rgba(255, 255, 255, 0.95)', 'padding': '15px',
        'borderRadius': '8px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.3)',
        'zIndex': 2000, 'border': '1px solid #bdc3c7', 'minWidth': '160px'
    }
    
    if 'matrix' in step_data:
        legend_content = [
            html.H4("Legenda", style={'marginTop': 0, 'marginBottom': '10px', 'fontSize': '15px', 'fontWeight': 'bold'}),
            html.Div([html.Span("■", style={'color': '#9b59b6', 'marginRight': '8px', 'fontSize': '18px'}), html.Span("Pivô (k)", style={'verticalAlign': 'top'})], style={'marginBottom': '5px'}),
            html.Div([html.Span("■", style={'color': '#3498db', 'marginRight': '8px', 'fontSize': '18px'}), html.Span("Origem (i)", style={'verticalAlign': 'top'})], style={'marginBottom': '5px'}),
            html.Div([html.Span("■", style={'color': '#e67e22', 'marginRight': '8px', 'fontSize': '18px'}), html.Span("Destino (j)", style={'verticalAlign': 'top'})]),
            html.Div([html.Span("■", style={'color': '#f1c40f', 'marginRight': '8px', 'fontSize': '18px', 'WebkitTextStroke': '1px #e74c3c'}), html.Span("Atualização", style={'verticalAlign': 'top'})], style={'marginTop': '5px'})
        ]
    else:
        legend_content = [
            html.H4("Legenda", style={'marginTop': 0, 'marginBottom': '10px', 'fontSize': '15px', 'fontWeight': 'bold'}),
            html.Div([html.Span("■", style={'color': '#e74c3c', 'marginRight': '8px', 'fontSize': '18px'}), html.Span("Vértice Atual", style={'verticalAlign': 'top'})], style={'marginBottom': '5px'}),
            html.Div([html.Span("■", style={'color': '#f39c12', 'marginRight': '8px', 'fontSize': '18px'}), html.Span("Fila / Pilha", style={'verticalAlign': 'top'})], style={'marginBottom': '5px'}),
            html.Div([html.Span("■", style={'color': '#27ae60', 'marginRight': '8px', 'fontSize': '18px'}), html.Span("Visitado", style={'verticalAlign': 'top'})], style={'marginBottom': '5px'}),
            html.Div([html.Span("▬", style={'color': '#9c3edc', 'marginRight': '8px', 'fontSize': '18px', 'fontWeight': 'bold'}), html.Span("Caminho", style={'verticalAlign': 'top'})]),
        ]

    return new_elements, status_msg, status_style, player_style, close_btn_style, sidebar_style, sidebar_content, legend_style, legend_content


# CALLBACK PARA O TESTE DO CAMINHO CURTO
@app.callback(
    Output('cyto-graph', 'elements', allow_duplicate=True),
    Output('path-result', 'children'),
    Input('btn-test-path', 'n_clicks'),
    State('path-start', 'value'),
    State('path-end', 'value'),
    State('anim-steps', 'data'),
    State('cyto-graph', 'elements'),
    State('graph-props', 'data'),
    prevent_initial_call=True
)
def destacar_caminho_curto(n_clicks, start, end, steps, elements, props):
    if not n_clicks or not start or not end: return dash.no_update
    
    # Pega os dados do último passo da animação
    final_step = steps[-1]
    if 'next_node' not in final_step: return dash.no_update
    
    dist_matrix = final_step['matrix']
    next_node_matrix = final_step['next_node']
    nodes_list = final_step['nodes_list']
    
    start, end = str(start).strip(), str(end).strip()
    
    if start not in nodes_list or end not in nodes_list:
        return dash.no_update, "Vértice não existe!"

    node_to_idx = {node_id: i for i, node_id in enumerate(nodes_list)}
    i, j = node_to_idx[start], node_to_idx[end]
    
    dist = dist_matrix[i][j]
    if dist == float('inf'): return dash.no_update, "Sem conexão!"

    # Reconstrói a lista de nós do caminho
    path_nodes = [start]
    curr = start
    while curr != end:
        curr = next_node_matrix[node_to_idx[curr]][node_to_idx[end]]
        path_nodes.append(curr)
    
    # Cria os pares (Origem, Destino) que compõem o caminho
    path_pairs = [(path_nodes[k], path_nodes[k+1]) for k in range(len(path_nodes) - 1)]
    is_dir = props.get('is_directed', True)

    new_elements = copy.deepcopy(elements)
    for el in new_elements:
        el['classes'] = el.get('classes', '').replace(' tree-edge', '').replace(' current', '')
        
        if 'source' not in el['data']:
            if el['data']['id'] in path_nodes:
                el['classes'] += ' current'
        
        else:
            u_el = el['data']['source']
            v_el = el['data']['target']
            
            for u_p, v_p in path_pairs:
                if is_dir:
                    if u_el == u_p and v_el == v_p:
                        el['classes'] += ' tree-edge'
                        break
                else:
                    if (u_el == u_p and v_el == v_p) or (u_el == v_p and v_el == u_p):
                        el['classes'] += ' tree-edge'
                        break
                
    return new_elements, f"Distância: {dist}"

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
    Output('legend-panel', 'style', allow_duplicate=True),
    Output('anim-sidebar', 'className', allow_duplicate=True),
    Input('btn-close-anim', 'n_clicks'),
    State('cyto-graph', 'elements'),
    prevent_initial_call=True
)
def fechar_animacao(n_clicks, elements):
    if not n_clicks: raise PreventUpdate
    
    new_elements = copy.deepcopy(elements)
    for el in new_elements:
        el['classes'] = el.get('classes', '').replace(' visited', '').replace(' frontier', '').replace(' current', '').replace(' tree-edge', '').replace(' floyd-pivot', '').replace(' floyd-source', '').replace(' floyd-target', '')
        
    sidebar_style_reset = {
        'display': 'none', 'flexDirection': 'column', 'position': 'absolute', 'top': '15px', 'right': '15px', 
        'backgroundColor': 'rgba(255, 255, 255, 0.95)', 'padding': '20px', 
        'borderRadius': '8px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.4)', 
        'zIndex': 2000, 'border': '1px solid #bdc3c7', 'overflow': 'hidden',
        'maxHeight': 'calc(100vh - 140px)'
    }
    
    return new_elements, [], {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, True, sidebar_style_reset, {'display': 'none'}, ''

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
        
        # Valida se o vértice sendo criado já existe
        exists = any(el['data']['id'] == node_id for el in elements if 'source' not in el['data'])
        if exists:
            return new_style, node_id, connect_to, weight, f"⚠️ O vértice '{node_id}' já existe!", dash.no_update, dash.no_update

        # Valida se o destino digitado realmente existe
        if connect_to:
            connect_to = str(connect_to).strip()
            dest_exists = any(el['data']['id'] == connect_to for el in elements if 'source' not in el['data'])
            if not dest_exists:
                return new_style, node_id, connect_to, weight, f"⚠️ O vértice destino '{connect_to}' não existe!", dash.no_update, dash.no_update

        new_elements = copy.deepcopy(elements)
        new_elements.append({'data': {'id': node_id, 'label': node_id}, 'position': {'x': 400, 'y': 300}})

        if connect_to:
            w = str(weight).strip() if weight is not None and str(weight).strip() != "" else '0'
            
            if not props['is_weighted'] and w != '0':
                 return new_style, node_id, connect_to, weight, "⚠️ O grafo atual é Não Ponderado. Altere para 'Ponderado' no menu Ações primeiro.", dash.no_update, dash.no_update

            base_class = (' undirected' if not props['is_directed'] else '')
            if not props['is_weighted']:
                base_class += ' unweighted'
                w = '0' 
            
            new_elements.append({'data': {'id': f'e_{node_id}_{connect_to}', 'source': node_id, 'target': connect_to, 'weight': w}, 'classes': base_class})

        new_style['display'] = 'none'
        new_counter = counter + 1 if node_id == str(counter) else counter

        return new_style, "", None, "", "", new_elements, new_counter
        
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# ==========================================
# LÓGICA PARA CARREGAR GRAFOS PRONTOS
# ==========================================
@app.callback(
    Output('cyto-graph', 'elements', allow_duplicate=True),
    Output('node-counter', 'data', allow_duplicate=True),
    Output('graph-props', 'data', allow_duplicate=True),
    Output('btn-orientado', 'style', allow_duplicate=True),
    Output('btn-ponderado', 'style', allow_duplicate=True),
    Input('btn-grafo-casa', 'n_clicks'),
    Input('btn-grafo-circulo', 'n_clicks'),
    Input('btn-grafo-floyd', 'n_clicks'),
    Input('btn-grafo-floyd2', 'n_clicks'),
    Input('btn-grafo-arvore', 'n_clicks'),
    State('anim-steps', 'data'),
    prevent_initial_call=True
)
def carregar_grafos_prontos(n_casa, n_circ, n_arv, n_floyd, n_floyd2, anim_steps):
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

    # --- FLOYD 1 (6V, Orientado, Com Pesos Negativos) ---
    elif trigger == 'btn-grafo-floyd':
        props = {'is_directed': True, 'is_weighted': True}
        el = [
            {'data': {'id': '1', 'label': '1'}, 'position': {'x': 150, 'y': 300}},
            {'data': {'id': '2', 'label': '2'}, 'position': {'x': 480, 'y': 80}},
            {'data': {'id': '3', 'label': '3'}, 'position': {'x': 350, 'y': 480}},
            {'data': {'id': '4', 'label': '4'}, 'position': {'x': 580, 'y': 250}},
            {'data': {'id': '5', 'label': '5'}, 'position': {'x': 800, 'y': 100}},
            {'data': {'id': '6', 'label': '6'}, 'position': {'x': 800, 'y': 400}},
        ]
        conexoes = [
            ('1', '2', '5'), ('1', '3', '2'), ('2', '4', '-3'),
            ('3', '4', '6'), ('4', '5', '4'), ('4', '6', '8'),
            ('5', '6', '-5'), ('6', '2', '7'), ('3', '1', '1'),
            ('5', '1', '10')
        ]
        for u, v, w in conexoes:
            el.append({'data': {'id': f'e_{u}_{v}', 'source': u, 'target': v, 'weight': w}, 'classes': ''})
            
        return el, 7, props, style_ativo, style_ativo

    # --- FLOYD 2 (10V) ---
    elif trigger == 'btn-grafo-floyd2':
        props = {'is_directed': True, 'is_weighted': True}
        el = [
            {'data': {'id': '1', 'label': '1'}, 'position': {'x': 100, 'y': 300}},
            {'data': {'id': '2', 'label': '2'}, 'position': {'x': 300, 'y': 150}},
            {'data': {'id': '3', 'label': '3'}, 'position': {'x': 300, 'y': 450}},
            {'data': {'id': '4', 'label': '4'}, 'position': {'x': 500, 'y': 150}},
            {'data': {'id': '5', 'label': '5'}, 'position': {'x': 521, 'y': 455}},
            {'data': {'id': '6', 'label': '6'}, 'position': {'x': 715, 'y': 151}},
            {'data': {'id': '7', 'label': '7'}, 'position': {'x': 725, 'y': 447}},
            {'data': {'id': '8', 'label': '8'}, 'position': {'x': 915, 'y': 299}},
            {'data': {'id': '9', 'label': '9'}, 'position': {'x': 574, 'y': 301}},
            {'data': {'id': '10', 'label': '10'}, 'position': {'x': 300, 'y': 300}},
        ]
        
        conexoes = [
            ('1', '2', '10'), ('1', '3', '5'), ('1', '10', '2'),
            ('2', '4', '1'), ('2', '9', '-2'), ('10', '2', '3'),
            ('3', '5', '2'), ('3', '10', '4'), ('10', '3', '1'),
            ('9', '4', '2'), ('9', '5', '8'), ('9', '8', '15'),
            ('4', '6', '10'), ('4', '5', '-5'), ('5', '7', '6'),
            ('6', '8', '2'), ('7', '8', '2'), ('6', '7', '-3'),
            ('10', '9', '12'), ('5', '6', '1'), ('7', '10', '20')
        ]
        
        for u, v, w in conexoes:
            el.append({'data': {'id': f'e_{u}_{v}', 'source': u, 'target': v, 'weight': w}, 'classes': ''})
            
        return el, 11, props, style_ativo, style_ativo

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

    return el, qtd + 1, props, style_inativo, style_inativo

# ===========================
# ATUALIZAR O TEXTO DO ZOOM
# ===========================
@app.callback(
    Output('zoom-label', 'children'),
    Input('zoom-slider', 'value')
)
def atualizar_texto_zoom(valor):
    return f"Ajuste de Zoom: {valor:.2f}x"

# ==========================================
# ALTERNADOR DE TEMA (MODO CLARO E ESCURO)
# ==========================================
@app.callback(
    Output('app-wrapper', 'className'),
    Output('cyto-graph', 'stylesheet'),
    Output('zoom-slider', 'marks'),
    Output('zoom-label', 'style'),
    Output('speed-slider', 'marks'),
    Output('speed-label', 'style'),
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
    
    # Atualiza as cores do Zoom
    novas_marcas_zoom = {
        0.15: {'label': '0.15x', 'style': {'color': cor_texto}},
        1: {'label': '1x', 'style': {'color': cor_texto}},
        2.5: {'label': '2.5x', 'style': {'color': cor_texto}}
    }
    estilo_label_zoom = {'fontWeight': 'bold', 'color': cor_texto, 'fontSize': '14px', 'marginBottom': '5px', 'display': 'block'}
    
    # Atualiza as cores da Velocidade
    novas_marcas_speed = {
        0: {'label': '0.5x', 'style': {'color': cor_texto}},
        1: {'label': '1x', 'style': {'color': cor_texto}},
        2: {'label': '2x', 'style': {'color': cor_texto}},
        3: {'label': '4x', 'style': {'color': cor_texto}}
    }
    estilo_label_speed = {'textAlign': 'center', 'width': '100%', 'fontWeight': 'bold', 'color': cor_texto, 'fontSize': '12px', 'marginBottom': '8px', 'textTransform': 'uppercase', 'letterSpacing': '1px'}
    
    return theme_class, current_style, novas_marcas_zoom, estilo_label_zoom, novas_marcas_speed, estilo_label_speed

# ==========================================
# EXIBIÇÃO DE MENSAGENS DA BARRA DE STATUS
# ==========================================
app.clientside_callback(
    """
    function(msg) {
        let statusBar = document.getElementById('status-bar');
        if (!statusBar) return window.dash_clientside.no_update;

        // Limpa qualquer cronômetro antigo
        if (window.statusTimeout) {
            clearTimeout(window.statusTimeout);
        }

        if (msg && msg !== "") {
            statusBar.style.display = 'block';
            
            let texto = statusBar.innerText || "";
            
            if (texto.includes("⚠️") || texto.includes("❌")) {
                window.statusTimeout = setTimeout(function() {
                    statusBar.style.display = 'none';
                }, 4000);
            }
            
        } else {
            statusBar.style.display = 'none';
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('dummy-unselect', 'data-timeout', allow_duplicate=True),
    Input('status-bar', 'children'),
    prevent_initial_call=True
)

# ==========================================
# AUTO-FOCUS E ENTER NO MODAL DE EDIÇÃO
# ==========================================
app.clientside_callback(
    """
    function(style) {
        if (style && style.display === 'block') {
            setTimeout(function() {
                let input = document.getElementById('edit-input');
                if (input) {
                    input.focus();
                    input.select(); // Seleciona o texto atual para sobrescrever direto
                    
                    input.onkeypress = function(e) {
                        if (e.key === 'Enter') {
                            document.getElementById('btn-save-edit').click();
                        }
                    };
                }
            }, 100);
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('dummy-unselect', 'data-focus', allow_duplicate=True),
    Input('edit-modal', 'style'),
    prevent_initial_call=True
)

# Ajusta o intervalo base (800ms) pela escala do slider
@app.callback(
    Output('anim-interval', 'interval'),
    Input('speed-slider', 'value')
)
def ajustar_velocidade_real(posicao_slider):
    mapa_velocidade = {0: 0.5, 1: 1.0, 2: 2.0, 3: 4.0}
    escala = mapa_velocidade.get(posicao_slider, 1.0)
    
    base_ms = 800
    return int(base_ms / escala)

# Controla a visibilidade e centraliza na tela
@app.callback(
    Output('speed-control-container', 'style'),
    Input('anim-steps', 'data'),
    prevent_initial_call=True
)
def toggle_speed_control(steps):
    if not steps or len(steps) == 0:
        return {'display': 'none'}
    
    return {
        'display': 'flex', 
        'flexDirection': 'column',
        'position': 'absolute', 
        'bottom': '20px', 
        'left': '300px', 
        'width': '220px', 
        'backgroundColor': 'rgba(255, 255, 255, 0.95)', 
        'padding': '10px 20px', 
        'borderRadius': '20px', 
        'boxShadow': '0 4px 15px rgba(0,0,0,0.3)', 
        'zIndex': 2000,
        'alignItems': 'center'
    }

# ===============================
# BOTÕES DE MAXIMIZAR E MINIMIZAR
# ===============================
@app.callback(
    Output('anim-sidebar', 'className'),
    Input('btn-win-min', 'n_clicks'),
    Input('btn-win-max', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_sidebar_size(n_min, n_max):
    trigger = ctx.triggered_id
    if trigger == 'btn-win-max':
        return 'maximized-sidebar'
    return ''

if __name__ == '__main__':
    app.run(debug=True, dev_tools_ui=False, dev_tools_props_check=False)
