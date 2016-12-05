import React, {Component} from 'react';
import moment from 'moment';
import axios from 'axios';

import Paper from 'material-ui/Paper';
import {Card, CardActions, CardHeader, CardMedia, CardTitle, CardText} from 'material-ui/Card';
import {List, ListItem, makeSelectable} from 'material-ui/List';
import Divider from 'material-ui/Divider';
import Toggle from 'material-ui/Toggle';
import Delete from 'material-ui/svg-icons/action/history';
import AddCircle from 'material-ui/svg-icons/content/add-circle';
import Settings from 'material-ui/svg-icons/action/settings';
import TrendingUp from 'material-ui/svg-icons/action/trending-up';
import {cyan900} from 'material-ui/styles/colors';

import {Grid, Row, Col} from 'react-flexbox-grid';

import Start from './start';
import Run from './run/run';


function PiDetails(props) {
  const { calorimeter } = props;
  const { name, serial, last_comm_time, current_ref_temp, current_sample_temp, is_active, has_active_runs } = calorimeter;
  return (
    <Card zDepth={1} style={{minHeight: '100%', marginRight: '0'}}>
      <CardHeader title={name} subtitle={"Serial Number: " + serial}
                  titleStyle={{fontSize: '120%', fontWeight: 'bold', wordWrap: 'break-word'}}
                  subtitleStyle={{wordWrap: 'break-word'}}
                  avatar="https://media1.popsugar-assets.com/files/thumbor/i77ERIFg9HTnqKt9u8Ro_e67qN8/fit-in/2048xorig/filters:format_auto-!!-:strip_icc-!!-/2014/07/28/910/n/1922507/e399c9429796a92f_robot/i/Robot.jpg"
      />
      <CardText style={{padding: '0 0 0 1em', margin: '0'}}>
          <Grid><Row>
            <Col xs={12} sm={12} md={12} lg={12}>
              <p style={{wordWrap: 'break-word'}}>
                Sample Cell: {Math.round(current_sample_temp * 10)/10}&deg;C. <br/>
                Reference Cell: {Math.round(current_ref_temp * 10)/10}&deg;C.
              </p>
            </Col>
            <Col xs={12} sm={12} md={12} lg={12}>
              <p style={{wordWrap: 'break-word'}}>
                This device is {is_active ? "connected" : "inactive"}.<br/>
                Last communication received: {moment(last_comm_time).fromNow()}.<br/>
                {has_active_runs ? "There is one running calorimetery job." : "There are no jobs running at the moment."}
              </p>
            </Col>
          </Row></Grid>
      </CardText>
    </Card>
  )
}


let SelectableList = makeSelectable(List);

export class ControlsList extends Component {
  constructor(props) {
    super(props);

    var value = 0;
    const {historyActive, activeRunActive, startNewRunActive, calibrateActive} = props;
    if(historyActive) {
      value = 0;
    } else if (activeRunActive) {
      value = 1;
    } else if (startNewRunActive) {
      value = 1;
    } else if (calibrateActive) {
      value = 2;
    }

    this.state = {
      value
    };
    this.onChange = this.onChange.bind(this);
  }

  onChange(event, index) {
    this.setState({value: index});
  }

  render() {
    const highlightColor = cyan900;
    const focusedStyle = {fontWeight: '900', color: cyan900};
    const unfocusedStyle = {cursor: 'pointer'};
    const paperStyle = {
      display: 'inline-block',
      float: 'left',
      width: '100%',
      marginTop: '0',
      paddingTop: '-0.5em',
    };
    const {autorefresh, toggleAutorefresh, activeRun, historyActive,
      activeRunActive, startNewRunActive, calibrateActive, setMenuItems} = this.props;

    return (
      <Paper zDepth={3} style={paperStyle}>
        <SelectableList value={this.state.value} onChange={this.onChange}>
          <ListItem primaryText="All Runs" leftIcon={<Delete color={historyActive ? highlightColor : null}/>}
                    style={historyActive ? focusedStyle : unfocusedStyle} value={0}
                    onTouchTap={setMenuItems.bind(null, true, false, false, false)}
          />
          {!!activeRun
            ? <ListItem primaryText={!!activeRun.name ? activeRun.name : `Run #${activeRun.id}`}
                        leftIcon={<TrendingUp color={activeRunActive ? highlightColor : null}/>}
                        style={activeRunActive ? focusedStyle : unfocusedStyle} value={1}
                        onTouchTap={setMenuItems.bind(null, false, false, true, false)}

          />
            : <ListItem primaryText="New Run"
                        leftIcon={<AddCircle color={startNewRunActive ? highlightColor : null}/>}
                        style={startNewRunActive ? focusedStyle : unfocusedStyle} value={1}
                        onTouchTap={setMenuItems.bind(null, false, true, false, false)}
          />
          }
          <ListItem primaryText="Calibrate" leftIcon={<Settings color={calibrateActive ? highlightColor : null}/>}
                    style={calibrateActive ? focusedStyle : unfocusedStyle} value={2}
                    onTouchTap={setMenuItems.bind(null, false, false, false, true)}
          />
          <Divider />
          <Toggle toggled={autorefresh} onToggle={toggleAutorefresh} labelPosition="right"
                  label={autorefresh ? "Auto-refresh is on."
                    : "Auto-refresh is off."}
                  labelStyle={{fontWeight: '400', color: 'grey'}}
                  style={{padding: '1em 0.5em 0em 1em'}}
          />
        </SelectableList>
      </Paper>
    )
  }
}


export default class Status extends Component {
  constructor(props) {
    super(props);
    const has_active_run = props.calorimeter.has_active_run;
    this.state = {
      autorefresh: true,
      autorefreshInt: null,
      historyActive: false,
      startNewRunActive: !has_active_run,
      activeRunActive: !!has_active_run,
      calibrateActive: false,
    };
    this.toggleAutorefresh = this.toggleAutorefresh.bind(this);
    this.setMenuItems = this.setMenuItems.bind(this);
    this.autorefresh = this.autorefresh.bind(this);
    this.renderMainContent = this.renderMainContent.bind(this);
  }

  componentDidMount() {
    this.autorefresh();
  }
  toggleAutorefresh() {
    this.setState({autorefresh: !this.state.autorefresh}, this.autorefresh);
  }
  setMenuItems(history, startNewRun, activeRun, calibrate) {
    this.setState({
      historyActive: history,
      startNewRunActive: startNewRun,
      activeRunActive: activeRun,
      calibrateActive: calibrate,
    })
  }
  autorefresh() {
    if(this.state.autorefresh) {
      const int = window.setInterval(
        () => {
          this.props.toggleLoading();
          axios.get('/api/status/?access_code=' + this.props.code)
            .then((response) => {
              this.props.changeCalorimeterStatus(response.data);
              this.props.changeAccessCode(response.data.access_code);
              this.props.toggleLoading();
            })
            .catch((error) => {
              console.log(error.response);
              this.props.toggleLoading();
            })
        },
        5000);
      this.setState({autorefreshInt: int});
    }
    else {
      window.clearInterval(this.state.autorefreshInt);
    }
  }

  renderMainContent() {
    var node;
    if(this.state.startNewRunActive) {
      node = <Start {...this.props} />;
    } else if( this.state.activeRunActive ) {
      node = <Run expanded={true} run={this.props.calorimeter.has_active_runs}
                  {...this.props} />
    }
    return (
      <div>
        {node}
      </div>
    );
  }

  render() {
    return (
      <Grid>
        <Row>
          <Col xs={6} sm={7} md={8} lg={8} style={{margin: '1em 0 0 0', zIndex: '1'}}>
            <PiDetails calorimeter={this.props.calorimeter}/>
          </Col>
          <Col xs={6} sm={5} md={4} lg={4} style={{margin: '1em 0 0 0', zIndex: '3'}}>
            <ControlsList historyActive={this.state.historyActive}
                          startNewRunActive={this.state.startNewRunActive}
                          calibrateActive={this.state.calibrateActive}
                          activeRunActive={this.state.activeRunActive}
                          activeRun={this.props.calorimeter.has_active_runs}
                          setMenuItems={this.setMenuItems}
                          toggleAutorefresh={this.toggleAutorefresh} autorefresh={this.state.autorefresh}
            />
          </Col>
          <Col xs={12} sm={12} md={12} lg={12} style={{marginTop: '0.45em', zIndex: '1'}}>
            {this.renderMainContent()}
          </Col>
        </Row>
      </Grid>
    )
  }
}