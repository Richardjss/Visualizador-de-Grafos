# layout.py
from dash import dcc, html
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc
from config import *

def create_layout():
    return html.Div(id='app-wrapper', className='light-theme', style=APP_WRAPPER_STYLE, children=[
        
        # ARMAZENAMENTO DA ANIMAÇÃO
        dcc.Store(id='anim-steps', data=[]),
        dcc.Store(id='anim-index', data=0),
        dcc.Interval(id='anim-interval', interval=800, disabled=True),
        dcc.Store(id='node-counter', data=1),
        dcc.Store(id='action-state', data={'mode': 'idle', 'source_node': None}),
        dcc.Store(id='selected-node', data=None),
        dcc.Store(id='graph-props', data={'is_directed': True, 'is_weighted': True}),
        dcc.Store(id='floyd-path-data', data={'matrix': [], 'nodes': []}),

        html.Div(id='top-menu-overlay', style={'display': 'none'}),
        
        html.Button(id='hidden-v-btn', style={'display': 'none'}),
        html.Button(id='hidden-e-btn', style={'display': 'none'}),
        html.Button(id='hidden-ctrl-s-btn', style={'display': 'none'}),
        dcc.Input(id='right-click-data', type='text', style={'display': 'none'}),
        html.Button(id='hidden-right-click-btn', style={'display': 'none'}),
        dcc.Input(id='dbl-click-data', type='text', style={'display': 'none'}),
        html.Button(id='hidden-dbl-click-btn', style={'display': 'none'}),

        html.Div(style=HEADER_STYLE, children=[
            html.Div("Visualizador de Grafos", style=TITLE_STYLE),
            
            html.Div(style=TOP_MENU_CONTAINER, children=[
                html.Button('☰ Ações', id='btn-toggle-acoes', style=BTN_GREEN_STYLE, className='hover-btn'),
                html.Div(id="menu-acoes", style=DROPDOWN_MENU_STYLE, children=[
                    html.Button('Adicionar Vértice', id='btn-add-node-menu', n_clicks=0, style=DROPDOWN_ITEM_STYLE, className='dropdown-item'),
                    html.Button('Não Ponderado', id='btn-ponderado', n_clicks=0, style=DROPDOWN_ITEM_STYLE, className='dropdown-item'),
                    html.Button('Não Orientado', id='btn-orientado', n_clicks=0, style=DROPDOWN_ITEM_STYLE, className='dropdown-item'),
                    html.Button('Limpar Tudo', id='btn-limpar', n_clicks=0, style=DROPDOWN_ITEM_STYLE, className='dropdown-item')
                ])
            ]),

            html.Div(style=TOP_MENU_CONTAINER, children=[
                html.Button('⚙ Algoritmos ▼', id='btn-toggle-algoritmos', style=BTN_GRAY_STYLE, className='hover-btn'),
                html.Div(id="menu-algoritmos", style=DROPDOWN_MENU_STYLE, children=[
                    html.Button('BFS', id='btn-bfs', n_clicks=0, style=DROPDOWN_ITEM_STYLE, className='dropdown-item'),
                    html.Button('DFS', id='btn-dfs', n_clicks=0, style=DROPDOWN_ITEM_STYLE, className='dropdown-item'),
                    html.Button([
                        html.Span('Algoritmo'), 
                        html.Br(), 
                        html.Span('Floyd-Warshall')
                    ], id='btn-floyd', n_clicks=0, style=DROPDOWN_ITEM_STYLE, className='dropdown-item')
                ])
            ]),
            
            html.Div(style=TOP_MENU_CONTAINER, children=[
                html.Button('📂 Arquivo', id='btn-toggle-arquivo', style=BTN_GRAY_STYLE, className='hover-btn'),
                html.Div(id="menu-arquivo", style=DROPDOWN_MENU_STYLE, children=[
                    html.Button('Salvar', id='btn-salvar-modal-trigger', n_clicks=0, style=DROPDOWN_ITEM_STYLE, className='dropdown-item'),
                    dcc.Upload(
                        id='upload-grafo',
                        children=html.Button('Importar', style=DROPDOWN_ITEM_STYLE, className='dropdown-item'),
                        style={'width': '100%', 'padding': '0', 'margin': '0', 'border': 'none', 'display': 'block', 'backgroundColor': 'transparent'},
                        multiple=False
                    ),
                    dcc.Download(id="download-grafo")
                ])
            ]),

            html.Div(style=TOP_MENU_CONTAINER, children=[
                html.Button('⬡ Grafos ▼', id='btn-toggle-grafos', style=BTN_GRAY_STYLE, className='hover-btn'),
                html.Div(id="menu-grafos", style=DROPDOWN_MENU_STYLE, children=[
                    html.Button('Casa (5V)', id='btn-grafo-casa', n_clicks=0, style=DROPDOWN_ITEM_STYLE, className='dropdown-item'),
                    html.Button('Círculo (8V)', id='btn-grafo-circulo', n_clicks=0, style=DROPDOWN_ITEM_STYLE, className='dropdown-item'),
                    html.Button('Árvore (15V)', id='btn-grafo-arvore', n_clicks=0, style=DROPDOWN_ITEM_STYLE, className='dropdown-item'),
                    html.Button('Floyd 1 (6V)', id='btn-grafo-floyd', n_clicks=0, style=DROPDOWN_ITEM_STYLE, className='dropdown-item'),
                    html.Button('Floyd 2 (10V)', id='btn-grafo-floyd2', n_clicks=0, style=DROPDOWN_ITEM_STYLE, className='dropdown-item'),
                    html.Button('Personalizado', id='btn-grafo-custom-trigger', n_clicks=0, style=DROPDOWN_ITEM_STYLE, className='dropdown-item'),
                ])
            ]),
            
            html.Div(style=TOP_MENU_CONTAINER, children=[
                html.Button('🛈 Info', id='btn-info', style=BTN_GREEN_STYLE, className='hover-btn')
            ]),
            
            html.Button(id='btn-theme-toggle', className='theme-btn', n_clicks=0, children=[
                html.Span("☀️", className='icon'),
                html.Span("🌙", className='icon'),
                html.Div(className='slider')
            ])
        ]),

        html.Div(id='canvas-wrapper', style=CANVAS_WRAPPER_STYLE, children=[
            html.Div(id='menu-overlay', style={'display': 'none', 'position': 'fixed', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 'zIndex': 999, 'cursor': 'default'}),

            html.Div(id='legend-panel', style={'display': 'none'}),

            html.Div(id='context-menu', style={'display': 'none'}, children=[
                html.Button('🟢 Criar Vértice', id='btn-add-node', style=CTX_BTN_STYLE, className='hover-btn'),
                html.Button('➜ Criar Aresta', id='btn-add-edge', style=CTX_BTN_STYLE, className='hover-btn'),
                html.Button('✏️ Renomear', id='btn-rename', style=CTX_BTN_STYLE, className='hover-btn'),
                html.Button('🔍 Detalhes', id='btn-details', style=CTX_BTN_STYLE, className='hover-btn'),
                html.Button('🗑️ Deletar', id='btn-delete', style={**CTX_BTN_STYLE, 'color': '#c0392b'}, className='hover-btn'),
                html.Button('❌ Fechar', id='btn-close-menu', style={**CTX_BTN_STYLE, 'backgroundColor': '#bdc3c7', 'marginBottom': '0'}, className='hover-btn')
            ]),

            html.Div(id='vertex-details-modal', style={'display': 'none', 'position': 'absolute', 'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)', 'zIndex': 3000, 'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '8px', 'boxShadow': '0px 0px 20px rgba(0,0,0,0.4)', 'minWidth': '320px'}, children=[
                html.H3(id='details-title', style={'marginTop': '0', 'color': '#2c3e50', 'borderBottom': '2px solid #27ae60', 'paddingBottom': '10px'}),
                html.Div(id='details-content', style={'marginTop': '15px'}),
                html.Button('Fechar', id='btn-close-details', style={'marginTop': '20px', 'width': '100%', 'padding': '10px', 'backgroundColor': '#34495e', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontWeight': 'bold'}, className='hover-btn')
            ]),

            html.Div(id='info-panel', style={'display': 'none', 'position': 'absolute', 'top': '15px', 'right': '15px', 'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.3)', 'zIndex': 2000, 'minWidth': '250px', 'maxHeight': '80%', 'overflowY': 'auto'}, children=[
                html.Div(id='info-panel-content')
            ]),

            html.Div(id='anim-sidebar', className='', style={'display': 'none'}, children=[
                html.Div(id='sidebar-resizer', className='resizer-handle'),
                
                html.Div(style={'position': 'absolute', 'top': '10px', 'right': '10px', 'display': 'flex', 'gap': '4px', 'zIndex': 3000}, children=[
                    html.Button("-", id='btn-win-min', title="Tamanho Padrão", className='win-btn'),
                    html.Button("□", id='btn-win-max', title="Maximizar Tela", className='win-btn')
                ]),
                
                html.Div(id='anim-sidebar-content', style={'display': 'flex', 'flexDirection': 'column', 'height': '100%', 'minHeight': '0'})
            ]),

            html.Div(id='dummy-unselect', style={'display': 'none'}),
            html.Div(id='multi-select-panel', style={'display': 'none'}, children=[
                html.Span(id='multi-select-text', style={'fontWeight': 'bold', 'color': '#2c3e50', 'fontSize': '14px', 'textAlign': 'center', 'width': '100%'}),
                html.Div(style={'display': 'flex', 'flexDirection': 'column', 'gap': '8px', 'width': '100%'}, children=[
                    html.Button('🗑️ Excluir', id='btn-delete-multi', style={'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'padding': '6px 12px', 'borderRadius': '4px', 'fontSize': '13px', 'fontWeight': 'bold', 'cursor': 'pointer', 'width': '100%'}, className='hover-btn'),
                    html.Button('✖ Cancelar', id='btn-cancel-multi', style={'backgroundColor': '#95a5a6', 'color': 'white', 'border': 'none', 'padding': '6px 12px', 'borderRadius': '4px', 'fontSize': '13px', 'fontWeight': 'bold', 'cursor': 'pointer', 'width': '100%'}, className='hover-btn')
                ])
            ]),

            html.Div(id='edge-context-menu', style={'display': 'none'}, children=[
                html.Button('✏️ Renomear', id='btn-rename-edge', style=CTX_BTN_STYLE, className='hover-btn'),
                html.Button('🗑️ Deletar', id='btn-delete-edge', style={**CTX_BTN_STYLE, 'color': '#c0392b'}, className='hover-btn'),
                html.Button('❌ Fechar', id='btn-close-edge-menu', style={**CTX_BTN_STYLE, 'backgroundColor': '#bdc3c7', 'marginBottom': '0'}, className='hover-btn')
            ]),

            # MODAL DE EDIÇÃO
            html.Div(id='edit-modal', style={'display': 'none', 'position': 'absolute', 'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)', 'zIndex': 2000, 'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0px 0px 15px rgba(0,0,0,0.3)'}, children=[
                html.H3("Editar Rótulo", style={'marginTop': '0'}),
                dbc.Input(id='edit-input', type='text', style={'marginBottom': '10px'}),
                html.Button('Salvar', id='btn-save-edit', style={'padding': '8px 15px', 'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 'cursor': 'pointer', 'fontWeight': 'bold', 'borderRadius': '4px'}, className='hover-btn'),
                html.Button('Cancelar', id='btn-cancel-edit', style={'padding': '8px 15px', 'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'cursor': 'pointer', 'fontWeight': 'bold', 'borderRadius': '4px', 'marginLeft': '10px'}, className='hover-btn')
            ]),

            # MODAL SALVAR
            html.Div(id='save-modal', style={'display': 'none', 'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 'backgroundColor': 'rgba(0,0,0,0.5)', 'zIndex': 3000, 'alignItems': 'center', 'justifyContent': 'center'}, children=[
                html.Div(style={'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '8px', 'width': '320px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.3)'}, children=[
                    html.H3("Salvar Grafo", style={'marginTop': '0', 'color': '#333', 'textAlign': 'center'}),
                    html.Label("Nome do arquivo:", style={'display': 'block', 'marginBottom': '8px', 'fontWeight': 'bold', 'color': '#555'}),
                    dbc.Input(id='save-filename', type='text', value='meu_grafo', style={'marginBottom': '20px'}),
                    html.Div(style={'display': 'flex', 'justifyContent': 'space-between'}, children=[
                        html.Button('Cancelar', id='btn-cancel-save', style={'padding': '10px 15px', 'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontWeight': 'bold', 'width': '45%'}, className='hover-btn'),
                        html.Button('Confirmar', id='btn-confirm-save', style={'padding': '10px 15px', 'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontWeight': 'bold', 'width': '45%'}, className='hover-btn')
                    ])
                ])
            ]),

            # MODAL GRAFO PERSONALIZADO
            html.Div(id='custom-graph-modal', style={'display': 'none', 'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 'backgroundColor': 'rgba(0,0,0,0.5)', 'zIndex': 3000, 'alignItems': 'center', 'justifyContent': 'center'}, children=[
                html.Div(style={'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '8px', 'width': '320px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.3)'}, children=[
                    html.H3("Círculo Personalizado", style={'marginTop': '0', 'color': '#333', 'textAlign': 'center'}),
                    html.Label("Quantidade de Vértices:", style={'display': 'block', 'marginBottom': '8px', 'fontWeight': 'bold', 'color': '#555'}),
                    dbc.Input(id='custom-graph-input', type='number', min=1, step=1, value=10, style={'marginBottom': '20px'}),
                    html.Div(style={'display': 'flex', 'justifyContent': 'space-between'}, children=[
                        html.Button('Cancelar', id='btn-cancel-custom', style={'padding': '10px 15px', 'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontWeight': 'bold', 'width': '45%'}, className='hover-btn'),
                        html.Button('Gerar Grafo', id='btn-confirm-custom', style={'padding': '10px 15px', 'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontWeight': 'bold', 'width': '45%'}, className='hover-btn')
                    ])
                ])
            ]),

            # MODAL BFS
            html.Div(id='bfs-modal', style={'display': 'none', 'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 'backgroundColor': 'rgba(0,0,0,0.5)', 'zIndex': 3000, 'alignItems': 'center', 'justifyContent': 'center'}, children=[
                html.Div(style={'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '8px', 'width': '320px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.3)'}, children=[
                    html.H3("Busca em Largura (BFS)", style={'marginTop': '0', 'color': '#333', 'textAlign': 'center'}),
                    html.Label("Escolha o Vértice Inicial:", style={'display': 'block', 'marginBottom': '8px', 'fontWeight': 'bold', 'color': '#555'}),
                    dbc.Input(id='bfs-start-node', type='text', placeholder="Digite o ID do vértice...", style={'marginBottom': '20px'}),
                    html.Div(style={'display': 'flex', 'justifyContent': 'space-between'}, children=[
                        html.Button('Cancelar', id='btn-cancel-bfs', style={'padding': '10px 15px', 'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontWeight': 'bold', 'width': '45%'}, className='hover-btn'),
                        html.Button('Iniciar BFS', id='btn-confirm-bfs', style={'padding': '10px 15px', 'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontWeight': 'bold', 'width': '45%'}, className='hover-btn')
                    ])
                ])
            ]),

            # MODAL DFS
            html.Div(id='dfs-modal', style={'display': 'none', 'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 'backgroundColor': 'rgba(0,0,0,0.5)', 'zIndex': 3000, 'alignItems': 'center', 'justifyContent': 'center'}, children=[
                html.Div(style={'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '8px', 'width': '320px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.3)'}, children=[
                    html.H3("Busca em Profundidade (DFS)", style={'marginTop': '0', 'color': '#333', 'textAlign': 'center'}),
                    html.Label("Escolha o Vértice Inicial:", style={'display': 'block', 'marginBottom': '8px', 'fontWeight': 'bold', 'color': '#555'}),
                    dbc.Input(id='dfs-start-node', type='text', placeholder="Digite o ID do vértice...", style={'marginBottom': '20px'}),
                    html.Div(style={'display': 'flex', 'justifyContent': 'space-between'}, children=[
                        html.Button('Cancelar', id='btn-cancel-dfs', style={'padding': '10px 15px', 'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontWeight': 'bold', 'width': '45%'}, className='hover-btn'),
                        html.Button('Iniciar DFS', id='btn-confirm-dfs', style={'padding': '10px 15px', 'backgroundColor': '#e67e22', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontWeight': 'bold', 'width': '45%'}, className='hover-btn')
                    ])
                ])
            ]),

            # MODAL ADICIONAR VÉRTICE
            html.Div(id='add-node-modal', style={'display': 'none', 'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 'backgroundColor': 'rgba(0,0,0,0.5)', 'zIndex': 3000, 'alignItems': 'center', 'justifyContent': 'center'}, children=[
                html.Div(style={'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '8px', 'width': '350px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.3)'}, children=[
                    html.H3("Adicionar Novo Vértice", style={'marginTop': '0', 'color': '#333', 'textAlign': 'center'}),
                    
                    html.Label("Nome/ID do Vértice:", style={'display': 'block', 'marginBottom': '5px', 'fontWeight': 'bold', 'color': '#555'}),
                    dbc.Input(id='add-node-id', type='text', placeholder="Ex: A, 1, v1...", style={'marginBottom': '15px'}),
                    
                    html.Label("Conectar a (Opcional):", style={'display': 'block', 'marginBottom': '5px', 'fontWeight': 'bold', 'color': '#555'}),
                    dbc.Input(id='add-node-connect-to', type='text', placeholder="Digite o ID do vértice...", style={'marginBottom': '15px'}),

                    html.Label("Peso da Aresta (Opcional):", style={'display': 'block', 'marginBottom': '5px', 'fontWeight': 'bold', 'color': '#555'}),
                    dbc.Input(id='add-node-weight', type='number', placeholder="0", style={'marginBottom': '10px'}),
                    
                    html.Div(id='add-node-error', style={'color': '#e74c3c', 'marginBottom': '15px', 'fontWeight': 'bold', 'fontSize': '14px', 'textAlign': 'center'}),
                    
                    html.Div(style={'display': 'flex', 'justifyContent': 'space-between'}, children=[
                        html.Button('Cancelar', id='btn-cancel-add-node', style={'padding': '10px 15px', 'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontWeight': 'bold', 'width': '45%'}, className='hover-btn'),
                        html.Button('Adicionar', id='btn-save-add-node', style={'padding': '10px 15px', 'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontWeight': 'bold', 'width': '45%'}, className='hover-btn')
                    ])
                ])
            ]),

            html.Div(id='status-bar', style={'display': 'none'}),

            html.Div(id='anim-player', style={
                'display': 'none', 'position': 'absolute', 'bottom': '20px', 'left': '50%', 'transform': 'translateX(-50%)',
                'backgroundColor': '#111', 'padding': '10px 25px', 'borderRadius': '30px',
                'boxShadow': '0 4px 15px rgba(0,0,0,0.6)', 'zIndex': 2000, 'alignItems': 'center', 'gap': '20px'
            }, children=[
                html.Button('⏮', id='btn-anim-start', title='Ir para o começo', className='player-btn'),
                html.Button('◀', id='btn-anim-prev', title='Voltar um passo', className='player-btn'),
                html.Button('⏸', id='btn-anim-play', title='Parar / Continuar', className='player-btn'),
                html.Button('▶', id='btn-anim-next', title='Avançar um passo', className='player-btn'),
                html.Button('⏭', id='btn-anim-end', title='Ir para o fim', className='player-btn'),
            ]),

            html.Div(id='anim-block-overlay', style={'display': 'none'}),
            html.Button('✖', id='btn-close-anim', title='Sair da Animação', style={'display': 'none'}),

            cyto.Cytoscape(
                id='cyto-graph', layout={'name': 'preset', 'fit': False}, zoom=1, 
                style={'width': '100%', 'height': '100%', 'backgroundColor': 'transparent'},
                stylesheet=STYLESHEET, elements=[], 
                minZoom=0.15, maxZoom=2.5, 
                wheelSensitivity=0.15,
                boxSelectionEnabled=True
            ),

            # Controle de Velocidade
            html.Div(
                id='speed-control-container', 
                style={'display': 'none'},
                children=[
                    html.Label("Velocidade", id='speed-label', style={'textAlign': 'center', 'width': '100%', 'fontWeight': 'bold', 'color': '#2c3e50', 'fontSize': '12px', 'marginBottom': '8px', 'textTransform': 'uppercase', 'letterSpacing': '1px'}),
                    dcc.Slider(
                        id='speed-slider',
                        min=0, max=3, step=1, 
                        marks={
                            0: {'label': '0.5x', 'style': {'color': '#2c3e50'}},
                            1: {'label': '1x', 'style': {'color': '#2c3e50'}},
                            2: {'label': '2x', 'style': {'color': '#2c3e50'}},
                            3: {'label': '4x', 'style': {'color': '#2c3e50'}}
                        },
                        value=1,
                    )
                ]
            ),

            # Controle de Zoom
            html.Div(
                id='zoom-control-container', 
                style={
                    'position': 'absolute', 'bottom': '20px', 'left': '20px', 
                    'width': '250px', 'backgroundColor': 'rgba(255, 255, 255, 0.9)', 
                    'padding': '10px 15px', 'borderRadius': '8px', 
                    'boxShadow': '0 4px 10px rgba(0,0,0,0.2)', 'zIndex': 1000
                },
                children=[
                    html.Label("Ajuste de Zoom: 1.00x", id='zoom-label', style={'fontWeight': 'bold', 'color': '#2c3e50', 'fontSize': '14px', 'marginBottom': '5px', 'display': 'block'}),
                    dcc.Slider(
                        id='zoom-slider',
                        min=0.15, max=2.5, step=0.05, value=1,       
                        marks={
                            0.15: {'label': '0.15x', 'style': {'color': '#2c3e50'}}, 
                            1: {'label': '1x', 'style': {'color': '#2c3e50'}}, 
                            2.5: {'label': '2.5x', 'style': {'color': '#2c3e50'}}
                        }, 
                        updatemode='drag'
                        
                    )
                ]
            )
        ])
    ])
