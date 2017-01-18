import React, {Component} from 'react';
import moment from 'moment';
import axios from 'axios';

import {Card, CardHeader, CardText} from 'material-ui/Card';
import RaisedButton from 'material-ui/RaisedButton';

import {Grid, Row, Col} from 'react-flexbox-grid';

import Controls from './controls';




function PiDetails(props) {
  const { calorimeter } = props;
  const { name, serial, last_comm_time, current_ref_temp, current_sample_temp, is_active, has_active_runs } = calorimeter;
  const title = (
    <div>
      <span style={{lineHeight: '22px', fontWeight: 'bold'}}>{name}</span>
      <RaisedButton label={is_active ? "Connected" : "Inactive"}
                    style={{cursor: '', padding: '0', height: '18px', marginLeft: '9px'}}
                    disabled={!is_active} primary={is_active}/>
    </div>
  );

  return (
    <Card zDepth={2}
          style={{minHeight: '100%', background: 'rgba(11, 30, 36, 0.9)',
                  margin: '0 -8888px 0 -8888px'}}>
      <div style={{padding: '0 8888px 0 8888px'}}>
        <CardHeader title={title} subtitle={"S/N: " + serial}
                    titleStyle={{wordWrap: 'break-word', color: '#E7E2E6'}}
                    subtitleStyle={{wordWrap: 'break-word', color: '#DDD6DB',}}
                    avatar="https://media1.popsugar-assets.com/files/thumbor/i77ERIFg9HTnqKt9u8Ro_e67qN8/fit-in/2048xorig/filters:format_auto-!!-:strip_icc-!!-/2014/07/28/910/n/1922507/e399c9429796a92f_robot/i/Robot.jpg"
        />
        <CardText style={{padding: '0 0 0 1em', margin: '0'}}>
            <Grid><Row>
              <Col xs={12} sm={12} md={12} lg={12}>
                <p style={{wordWrap: 'break-word', color: '#E7E2E6'}}>
                  Sample Cell: {Math.round(current_sample_temp * 10)/10}&deg;C. <br/>
                  Reference Cell: {Math.round(current_ref_temp * 10)/10}&deg;C.
                </p>
              </Col>
              <Col xs={12} sm={12} md={12} lg={12}>
                <p style={{wordWrap: 'break-word', color: '#E7E2E6',}}>
                  This device is {is_active ? "connected" : "inactive"}.<br/>
                  Last communication received: {moment(last_comm_time).fromNow()}.<br/>
                  {has_active_runs ? "There is one running calorimetery job." : "There are no jobs running at the moment."}
                </p>
              </Col>
            </Row></Grid>
        </CardText>
      </div>
    </Card>
  )
}


export default class Status extends Component {
  constructor(props) {
    super(props);
    this.state = {
      autorefresh: true,
      autorefreshInt: null
    };
    this.refresh = this.refresh.bind(this);
    this.toggleAutorefresh = this.toggleAutorefresh.bind(this);
    this.setMenuItems = this.setMenuItems.bind(this);
    this.autorefresh = this.autorefresh.bind(this);
  }

  componentDidMount() {
    this.autorefresh();
  }
  componentWillUnmount() {
    if(!!this.state.autorefreshInt) {
      window.clearInterval(this.state.autorefreshInt);
    }
  }
  toggleAutorefresh() {
    this.setState({autorefresh: !this.state.autorefresh}, this.autorefresh);
  }
  setMenuItems(history, activeOrStartRun, calibrate) {
    this.setState({
      historyActive: history,
      activeOrStartRunActive: activeOrStartRun,
      calibrateActive: calibrate,
    })
  }
  refresh() {
    this.props.toggleLoading();
    axios.get('/api/status/?access_code=' + this.props.code)
      .then((response) => {
        this.props.toggleLoading();
        this.props.changeCalorimeterStatus(response.data);
        this.props.changeAccessCode(response.data.access_code);
      })
      .catch((error) => {
        this.props.toggleLoading();
        console.log(error.response);
      })
  }
  autorefresh() {
    if(this.state.autorefresh) {
      this.refresh();
      const int = window.setInterval(this.refresh, 10000);
      this.setState({ autorefreshInt: int });
    }
    else {
      window.clearInterval(this.state.autorefreshInt);
    }
  }


  render() {
    return (
      <Grid style={{minWidth: '100%', overflowX: 'hidden', overflowY: 'hidden'}}>
        <Row>
          <Col xs={12} sm={12} md={10} lg={8} mdOffset={1} lgOffset={2}>
            <Row>
              <Col xs={6} sm={7} md={8} lg={8} style={{margin: '0', zIndex: '2'}}>
                <div style={{position: 'relative'}}>
                  <PiDetails calorimeter={this.props.calorimeter}/>
                </div>
              </Col>
              <Col xs={6} sm={5} md={4} lg={4} style={{margin: '1em 0 0 0', zIndex: '5', transform: 'translateX(1em) scale(1.025, 1.025)', }}>
                <Controls {...this.props}
                          toggleAutorefresh={this.toggleAutorefresh} autorefresh={this.state.autorefresh}
                />
              </Col>
              <br style={{clear: 'both'}} />
              <Col xs={12} sm={12} md={12} lg={12} style={{margin: '-1.5em 0 1.5em 0', zIndex: '1'}}>
                {React.Children.map( this.props.children, (child) => React.cloneElement(child, {
                  setMenuItems: this.setMenuItems,
                  autorefresh: this.state.autorefresh,
                  statusRefresh: this.refresh,
                  ...this.props,
                }))}
              </Col>
            </Row>
            </Col>
        </Row>
      </Grid>
    )
  }
}