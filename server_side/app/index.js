import React from 'react';
import ReactDOM from 'react-dom';
import axios from 'axios';
import Router from 'react-router/lib/Router';
import Route from 'react-router/lib/Route';
import IndexRoute from 'react-router/lib/IndexRoute';
import browserHistory from 'react-router/lib/browserHistory';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';

import injectTapEventPlugin from 'react-tap-event-plugin';

import Main from './components/main.js';
import Status from './components/status';
import DefaultContainer from './containers/defaultcontainer';
import CalibrateContainer from './containers/calibratecontainer';
import AllRunsContainer from './containers/allrunscontainer';

injectTapEventPlugin();

const Routes = () => (
  <Router history={browserHistory}>
    <Route path="/" component={Main}>
      <Route component={Status}>

        <IndexRoute components={DefaultContainer} />
        <Route path="history/:run_id/" components={AllRunsContainer} />
        <Route path="history" components={AllRunsContainer} />
        <Route path="calibrate" components={CalibrateContainer} />

      </Route>
    </Route>
  </Router>
);

const App = () => (
  <MuiThemeProvider>
      <Routes />
  </MuiThemeProvider>
);


axios.defaults.headers.common['X-CSRFToken'] = window.csrf_token;
axios.defaults.headers.post['X-CSRFToken'] = window.csrf_token;
axios.defaults.headers.put['X-CSRFToken'] = window.csrf_token;


ReactDOM.render(
    <App />,
    document.getElementById('root')
);