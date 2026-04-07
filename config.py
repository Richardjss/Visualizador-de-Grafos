# config.py

STYLESHEET = [
    {'selector': 'node', 'style': {
        'content': 'data(label)', 'text-valign': 'center', 'text-halign': 'center',
        'background-color': '#2c3e50', 'color': 'orange', 'font-size': '18px',
        'font-weight': 'bold', 'width': '45px', 'height': '45px',
        'border-width': 2, 'border-color': '#1a252f'
    }},

    # CORES DA ANIMAÇÃO
    {'selector': '.visited', 'style': {
        'background-color': '#27ae60', 'color': 'white', 'border-color': '#2ecc71',
        'transition-property': 'background-color, border-color', 'transition-duration': '0.3s'
    }},
    {'selector': '.frontier', 'style': {
        'background-color': '#f39c12', 'color': 'white', 'border-color': '#f1c40f',
        'transition-property': 'background-color, border-color', 'transition-duration': '0.3s'
    }},
    {'selector': '.current', 'style': {
        'background-color': '#e74c3c', 'color': 'white', 'border-color': '#c0392b',
        'border-width': 4, 'width': '55px', 'height': '55px', 'font-size': '22px',
        'transition-property': 'background-color, width, height', 'transition-duration': '0.3s'
    }},

    {'selector': 'edge', 'style': {
        'curve-style': 'bezier',
        'label': 'data(weight)',
        'color': '#c0392b',
        'font-size': '14px',
        'font-weight': 'bold',
        'text-background-opacity': 1,
        'text-background-color': '#ffffff',
        'text-background-padding': '3px',
        'text-margin-y': -15,
        'line-color': '#95a5a6',
        'target-arrow-shape': 'triangle',
        'target-arrow-color': '#95a5a6',
       
    }},

    {'selector': '.undirected', 'style': {'target-arrow-shape': 'none'}},

    # ESTILO PARA ITENS SELECIONADOS
    {'selector': ':selected', 'style': {
        'border-width': '4px', 'border-color': '#2980b9',
        'background-color': '#3498db', 'line-color': '#3498db',
        'target-arrow-color': '#3498db', 'source-arrow-color': '#3498db'
    }},
    # ESTILO DA CAIXA DE SELEÇÃO
    {'selector': 'core', 'style': {
        'selection-box-color': '#3498db',
        'selection-box-opacity': 0.2,
        'selection-box-border-color': '#2980b9',
        'selection-box-border-width': 1,
        'active-bg-color': '#3498db'
    }}
]

CTX_BTN_STYLE = {
    'display': 'block', 'width': '100%', 'padding': '8px', 'marginBottom': '5px',
    'cursor': 'pointer', 'border': 'none', 'backgroundColor': '#ecf0f1', 
    'textAlign': 'left', 'fontWeight': 'bold', 'borderRadius': '3px',
    'boxSizing': 'border-box'
}

APP_WRAPPER_STYLE = {
    'height': '100vh', 'width': '100vw', 'margin': 0, 
    'backgroundColor': '#1a1a1a', 
    'display': 'flex', 'flexDirection': 'column', 
    'fontFamily': 'sans-serif', 'boxSizing': 'border-box'
}

HEADER_STYLE = {
    'height': '70px', 'display': 'flex', 'alignItems': 'center',
    'padding': '0 15px', 'backgroundColor': '#1a1a1a',
    'justifyContent': 'flex-start'
}

TITLE_STYLE = {
    'color': 'white', 'fontSize': '22px', 'fontWeight': 'bold',
    'marginRight': '40px', 'letterSpacing': '0.5px'
}

TOP_MENU_CONTAINER = {
    'position': 'relative', 'marginRight': '10px'
}

BTN_GREEN_STYLE = {
    'backgroundColor': '#27ae60', 
    'color': 'white', 'border': 'none', 'padding': '10px 15px', 
    'fontSize': '16px', 'fontWeight': 'bold', 'borderRadius': '4px', 
    'cursor': 'pointer', 'display': 'flex', 'alignItems': 'center', 'gap': '5px',
    'boxShadow': '0 2px 4px rgba(0,0,0,0.2)'
}

BTN_GRAY_STYLE = {
    'backgroundColor': '#666', 
    'color': 'white', 'border': 'none', 'padding': '10px 15px', 
    'fontSize': '16px', 'fontWeight': 'bold', 'borderRadius': '4px', 
    'cursor': 'pointer', 'display': 'flex', 'alignItems': 'center', 'gap': '5px',
    'boxShadow': '0 2px 4px rgba(0,0,0,0.2)'
}

DROPDOWN_MENU_STYLE = {
    'position': 'absolute', 'top': '50px', 'left': '0',
    'backgroundColor': '#333', 'padding': '8px', 'borderRadius': '4px', 
    'boxShadow': '0px 4px 10px rgba(0,0,0,0.5)', 'display': 'none', 
    'zIndex': 1000, 'minWidth': '140px', 'flexDirection': 'column', 'gap': '5px'
}

DROPDOWN_ITEM_STYLE = {
    'width': '100%', 'padding': '10px', 'backgroundColor': '#444',
    'color': 'white', 'border': 'none', 'textAlign': 'center',
    'fontWeight': 'bold', 'borderRadius': '3px', 'cursor': 'pointer',
    'transition': 'background-color 0.2s', 'boxSizing': 'border-box'
}

CANVAS_WRAPPER_STYLE = {
    'flexGrow': 1, 'margin': '0 15px 15px 15px',
    'backgroundColor': '#f2f2f2', 'position': 'relative',
    'borderRadius': '4px', 'overflow': 'hidden',
    'boxShadow': 'inset 0 0 10px rgba(0,0,0,0.1)'
}