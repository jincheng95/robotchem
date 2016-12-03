import React from 'react';
import ReactDOM from 'react-dom';
import {Router, Route, IndexRoute, browserHistory} from 'react-router';
import injectTapEventPlugin from 'react-tap-event-plugin';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';

import Main from './components/main.js';
import Status from './components/status';

const Routes = () => (
  <Router history={browserHistory}>
    <Route path="/" component={Main}>
      <Route path="status" component={Status} />
    </Route>
  </Router>
);

const App = () => (
  <MuiThemeProvider>
      <Routes />
  </MuiThemeProvider>
);

injectTapEventPlugin();
ReactDOM.render(
    <App />,
    document.getElementById('root')
);