import React, {Component} from 'react';
import AppBar from 'material-ui/AppBar';
import {teal300, cyan50} from 'material-ui/styles/colors';
import IconButton from 'material-ui/IconButton';
import LinearProgress from 'material-ui/LinearProgress';
import Dashboard from 'material-ui/svg-icons/action/dashboard';
import {Grid, Row, Cell} from 'react-inline-grid';

import Access from './access';

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
      access_code: '',
      calorimeter: null,
      loading: false,
      accessCodeEntered: false,
    };
    this.changeAccessCode = this.changeAccessCode.bind(this);
    this.changeCalorimeterStatus = this.changeCalorimeterStatus.bind(this);
    this.toggleLoading = this.toggleLoading.bind(this);
  }

  changeAccessCode(code) {
    this.setState({access_code: code, accessCodeEntered: true});
  }
  changeCalorimeterStatus(data) {
    this.setState({calorimeter: data});
  }
  toggleLoading(){
    this.setState({loading: !this.state.loading});
  }

  render() {
    var clonePropsFunction = (child) => React.cloneElement(child, {
        changeAccessCode: this.changeAccessCode,
        changeCalorimeterStatus: this.changeCalorimeterStatus,
        code: this.state.access_code,
        toggleLoading: this.toggleLoading,
        calorimeter: this.state.calorimeter,
    });
    var clonedChildren = React.Children.map( this.props.children, clonePropsFunction );
    return (
      <div>
        <TitleBar/>
        {this.state.loading
        ? <LinearProgress style={{backgroundColor: teal300}} color={cyan50}
                        mode="indeterminate" />
        : <LinearProgress style={{backgroundColor: teal300}} color={cyan50}
                        value={0} mode="determinate"/>
        }
        {this.state.access_code
          ? clonedChildren
          : clonePropsFunction(<Access />)
        }
      </div>
    );
  }
}