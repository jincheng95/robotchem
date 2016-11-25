import React from 'react';
import ReactDOM from 'react-dom';
import injectTapEventPlugin from 'react-tap-event-plugin';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import Main from './components/main.js';

const App = () => (
    <MuiThemeProvider>
        <Main />
    </MuiThemeProvider>
);

injectTapEventPlugin();
ReactDOM.render(
    <App />,
    document.getElementById('root')
);