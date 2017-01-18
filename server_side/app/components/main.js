import React, {Component} from 'react';
import isEmpty from 'lodash/isEmpty';
import AppBar from 'material-ui/AppBar';
import {teal300, cyan50} from 'material-ui/styles/colors';
import IconButton from 'material-ui/IconButton';
import LinearProgress from 'material-ui/LinearProgress';
import Dashboard from 'material-ui/svg-icons/action/dashboard';

import {Grid, Row, Col} from 'react-flexbox-grid';

import Access from './access';
import Refreshing from './refreshing';

const TitleBar = (props) => (
  <AppBar title="RoboFlux"
          style={{backgroundColor: teal300}}
          titleStyle={{fontFamily: "'Patua One', cursive", fontSize: "200%"}}
          iconElementLeft={<IconButton> <Dashboard/> </IconButton>}/>
);

export default class Main extends Component {
  constructor(props) {
    super(props);
    this.state = {
      // access_code: '123456',
      // calorimeter: {
      //   access_code: "123456",
      //   creation_time: "2016-12-02T23:17:28.683866Z",
      //   current_ref_temp: 20.12,
      //   current_sample_temp: 20.30,
      //   id: 1,
      //   is_active: false,
      //   last_comm_time: "2016-12-02T23:17:27Z",
      //   last_changed_time: "2016-12-03T00:00:48.462929Z",
      //   name: "RPI3",
      //   serial: "2323423y40hi993240934"
      // },
      access_code: window.localStorage.getItem('access_code') || '',
      calorimeter: null,
      loading: false,
      accessCodeEntered: false,
    };
    this.changeAccessCode = this.changeAccessCode.bind(this);
    this.changeCalorimeterStatus = this.changeCalorimeterStatus.bind(this);
    this.toggleLoading = this.toggleLoading.bind(this);
  }

  changeAccessCode(code, remove) {
    this.setState({access_code: code, accessCodeEntered: true});
    try {
      window.localStorage.setItem('access_code', code);
      if(!!remove) {
        window.localStorage.removeItem('access_code');
      }
    }
  }
  changeCalorimeterStatus(data) {
    this.setState({calorimeter: data});
  }
  toggleLoading(){
    this.setState({loading: !this.state.loading});
  }

  render() {
    const clonePropsFunction = (element) => React.cloneElement(element, {
        changeAccessCode: this.changeAccessCode,
        changeCalorimeterStatus: this.changeCalorimeterStatus,
        code: this.state.access_code,
        toggleLoading: this.toggleLoading,
        calorimeter: this.state.calorimeter,
    });
    const clonedChildren = React.Children.map( this.props.children, clonePropsFunction );
    const hasCalorimeterInfo = !isEmpty(this.state.calorimeter);
    return (
      <Grid style={{width: '100%'}}>
        <Row>
          <Col xs={12} sm={12} md={12} lg={12}>
            <TitleBar/>
            {this.state.loading
            ? <LinearProgress style={{backgroundColor: teal300}} color={cyan50}
                            mode="indeterminate" />
            : <LinearProgress style={{backgroundColor: teal300}} color={cyan50}
                            value={0} mode="determinate"/>
            }
          </Col>
        </Row>
        <Row>
          <Col xs={12} sm={12} md={12} lg={12}>
            {hasCalorimeterInfo
              ? <div>{clonedChildren}</div>
              : clonePropsFunction(<Access isLoading={this.state.isLoading}/>) }
          </Col>
      </Row>
      </Grid>
    );
  }
}