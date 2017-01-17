import React, {Component} from 'react';
import withRouter from 'react-router/lib/withRouter';

import Paper from 'material-ui/Paper';
import {List, ListItem} from 'material-ui/List';
import Divider from 'material-ui/Divider';
import Toggle from 'material-ui/Toggle';

import History from 'material-ui/svg-icons/action/history';
import AddCircle from 'material-ui/svg-icons/content/add-circle';
import Settings from 'material-ui/svg-icons/action/settings';
import CircularProgress from 'material-ui/CircularProgress';
import {cyan900} from 'material-ui/styles/colors';


class Controls extends React.PureComponent {
  constructor(props, context) {
    super(props, context);
    this.goTo = this.goTo.bind(this);
    this.isActiveURI = this.isActiveURI.bind(this);
    this.renderListItem = this.renderListItem.bind(this);
  }

  isActiveURI(uri) {
    const raw_uri = uri.replace('/', '');
    const raw_current_location = this.props.location.pathname.replace('/', '');
    return raw_uri == raw_current_location;
  }
  goTo(uri) {
    if(!this.isActiveURI(uri)) {
      this.props.router.push(uri);
    }
  }

  renderListItem(title, route, icon) {
    const is_active = this.isActiveURI(route);
    const highlightedStyle = {
        fontWeight: 900,
        borderLeft: `solid 15px ${cyan900}`,
    };
    return (
      <ListItem onTouchTap={this.goTo.bind(null, route)}
                key={route} primaryText={title}
                style={is_active ? highlightedStyle : {paddingLeft: '15px'}}
                leftIcon={icon} />
    )
  }

  render() {
    const paperStyle = {
      display: 'inline-block',
      float: 'left',
      width: '100%',
      marginTop: '0',
      paddingTop: '-0.5em',
    };
    const { autorefresh, toggleAutorefresh } = this.props;
    const { has_active_runs } = this.props.calorimeter;

    return (
      <Paper zDepth={4} style={paperStyle}>
        <List>
          {!! has_active_runs
            ? this.renderListItem(!!has_active_runs.name ? has_active_runs.name : `Run #${has_active_runs.id}`,
                                  '/', <CircularProgress size={30}/>)
            : this.renderListItem("New Run", "/", <AddCircle />)
          }
          {this.renderListItem('History', '/history/', <History />)}
          {this.renderListItem('Calibrate', '/calibrate/', <Settings />)}
          <Divider />
          <Toggle toggled={autorefresh} onToggle={toggleAutorefresh} labelPosition="right"
                  label={autorefresh ? "Auto-refresh is on." : "Auto-refresh is off."}
                  labelStyle={{fontWeight: '400', color: 'grey'}}
                  style={{padding: '1em 0.5em 0em 1em'}}
          />
        </List>
      </Paper>
    )
  }
}

export default withRouter(Controls);