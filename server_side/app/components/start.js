import React, {Component} from 'react';
import axios from 'axios';
import RaisedButton from 'material-ui/RaisedButton';
import FlatButton from 'material-ui/FlatButton';
import Slider from 'material-ui/Slider';
import TextField from 'material-ui/TextField';
import Paper from 'material-ui/Paper';
import {Step, Stepper, StepLabel, StepContent} from 'material-ui/Stepper';
import {Table, TableBody} from 'material-ui/Table';

import validateEmail from '../utils/validate_email';
import TwoColumnRow from './TwoColumnRow';
import Refreshing from './refreshing';

export default class Start extends Component {
  constructor(props) {
    super(props);
    const {current_sample_temp} = this.props.calorimeter;
    var start_temp = current_sample_temp > 99 ? 99 : Math.round(props.calorimeter.current_sample_temp);
    this.state = {
      step: 0,
      start_temp: start_temp,
      target_temp: start_temp + 1,
      ramp_rate: 1,
      nickname: "",
      email: "",
      showInvalidEmailMessage: false,
      isLoading: false,
    };
    this.handleNext = this.handleNext.bind(this);
    this.handlePrev = this.handlePrev.bind(this);
    this.renderStepActions = this.renderStepActions.bind(this);
    this.changeStartTemp = this.changeStartTemp.bind(this);
    this.changeTargetTemp = this.changeTargetTemp.bind(this);
    this.changeRampRate = this.changeRampRate.bind(this);
    this.submit = this.submit.bind(this);
  }

  changeStartTemp(event, val) {
    const start_temp = Math.round(val*100);
    if( this.state.target_temp < start_temp ) {
      this.setState({target_temp: start_temp + 1})
    }
    this.setState({start_temp});
  }
  changeTargetTemp(event, val) {
    var temp = val * 100;
    if(temp < this.state.start_temp || (temp - this.state.start_temp) < 1){
      temp = this.state.start_temp + 1;
    }
    this.setState({target_temp: Math.round(temp)});
  }
  changeRampRate(event, rate) {
    this.setState({ramp_rate: rate})
  }

  handlePrev() {
    this.setState({step: this.state.step - 1});
  }
  handleNext() {
    const {email, step} = this.state;
    if( step === 2 && email != "" && !validateEmail(email) ){
      this.setState({showInvalidEmailMessage: true});
    } else if ( step === 3 ){
      this.submit();
    } else {
      this.setState({step: step + 1, showInvalidEmailMessage: false});
    }
  }
  submit() {
    const {start_temp, target_temp, ramp_rate, nickname, email} = this.state;
    const {calorimeter, code, toggleLoading, statusRefresh} = this.props;
    const {id} = calorimeter;
    toggleLoading();
    this.setState({isLoading: true});
    axios.post('/api/runs/', {
      access_code: code,
      calorimeter: id,
      start_temp,
      target_temp,
      ramp_rate,
      nickname,
      email,
    }).then((response) => {
      toggleLoading();
      statusRefresh();
    }).catch((error) => {
      toggleLoading();
      console.log(error.response);
    });
  }

  renderStepActions(renderedStep) {
    const { step } = this.state;
    var label;
    if(step === 3){
      label = "Start Run";
    } else if (step === 2) {
      label = "Review Your Run";
    } else {
      label = "Next";
    }
    return (
      <div style={{margin: '12px 0'}}>
        <RaisedButton
          label={label}
          disableTouchRipple={true}
          disableFocusRipple={true}
          primary={step !== 3}
          secondary={step === 3}
          onTouchTap={this.handleNext}
          style={{marginRight: 12}}
        />
        {renderedStep > 0 && (
          <FlatButton
            label="Back"
            disabled={step === 0}
            disableTouchRipple={true}
            disableFocusRipple={true}
            onTouchTap={this.handlePrev}
          />
        )}
      </div>
    );
  }

  render() {
    if(this.state.isLoading) {
      return (
        <Refreshing size={50} message="Submitting... One moment please."/>
      )
    }

    const {step, start_temp, target_temp, ramp_rate, nickname, email, showInvalidEmailMessage} = this.state;

    return (
      <Paper zDepth={1}>
          <Stepper activeStep={step} orientation="vertical" margin="auto">

              <Step>
                <StepLabel>Select start and end temperatures</StepLabel>
                <StepContent>
                  <h4>Starting at {start_temp} &deg;C.</h4>
                  <Slider value={start_temp / 100} onChange={this.changeStartTemp}/>
                  <h4>Finishing at {target_temp} &deg;C.</h4>
                  <Slider value={target_temp / 100} onChange={this.changeTargetTemp}/>
                  {this.renderStepActions(0)}
                </StepContent>
              </Step>

              <Step>
                <StepLabel>Decide the rate at which your sample is heated</StepLabel>
                <StepContent style={{paddingRight: '0.5em'}}>
                  <h4>Heating at {Math.round(ramp_rate * 100)}% power.</h4>
                  <p>An explanation of overshoots, ramp rate, theoretical maximum power, etc.</p>
                  <div style={{marginRight: '1em'}}>
                    <Slider value={ramp_rate} onChange={this.changeRampRate}/>
                  </div>
                  {this.renderStepActions(1)}
                </StepContent>
              </Step>

              <Step>
                <StepLabel>Additional options</StepLabel>
                <StepContent>
                  <TextField floatingLabelText="Give your run a name!" style={{marginTop: '4px'}}
                             value={nickname} onChange={(event) => this.setState({nickname: event.target.value})}
                  />
                  <p className="text-muted">(optional)</p>

                  <TextField floatingLabelText="Enter an email address"
                             value={email} onChange={(event) => this.setState({email: event.target.value})}
                             errorText={showInvalidEmailMessage ? "Please enter an valid email address, or leave it blank." : null}
                  />
                  <p className="text-muted">
                    When your calorimeter run has finished, <br/>
                    we can send you an email with a link to the results page. <br/>
                    (optional)
                  </p>
                  {this.renderStepActions(2)}
                </StepContent>
              </Step>

              <Step>
                <StepLabel>Overview</StepLabel>
                <StepContent>
                  <Table>
                    <TableBody>
                      {!!nickname && <TwoColumnRow title="Name" value={nickname}/>}
                      <TwoColumnRow title="Starting temperature" value={start_temp + "°C"}/>
                      <TwoColumnRow title="Target temperature" value={target_temp + "°C"}/>
                      <TwoColumnRow title="Power output" value={Math.round(ramp_rate * 100) + "%"}/>
                      {!!email && <TwoColumnRow title="Notify when done" value={email}/>}
                    </TableBody>
                  </Table>
                  {this.renderStepActions(3)}
                </StepContent>
              </Step>

          </Stepper>
        </Paper>
    );
  }
}