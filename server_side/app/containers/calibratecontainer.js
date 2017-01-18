import React, { Component } from 'react';
import axios from 'axios';

import Card from 'material-ui/Card/Card';
import CardText from 'material-ui/Card/CardText';
import FlatButton from 'material-ui/FlatButton';
import RaisedButton from 'material-ui/RaisedButton';
import TextField from 'material-ui/TextField';

export default class CalibrateContainer extends Component {
  constructor(props) {
    super(props);
    this.state = {
      calorimeter: props.calorimeter,
      changed: false,
    };
    this.onFieldChange = this.onFieldChange.bind(this);
    this.renderTextField = this.renderTextField.bind(this);
    this.submit = this.submit.bind(this);
  }

  onFieldChange(field, event, newValue) {
    let changes = {};
    changes[field] = newValue;
    this.setState({
      changed: true,
      calorimeter: {...this.state.calorimeter, ...changes}
    });
  }

  submit() {
    const { toggleLoading, statusRefresh } = this.props;
    toggleLoading();
    axios.put('/api/status/', this.state.calorimeter)
      .then((response) => {
        toggleLoading();
        statusRefresh();
      })
      .catch((error) => {
        toggleLoading();
      })
  }

  renderTextField(field, floatingLabel, fixedLabel) {
    return (
      <div style={{minWidth: '80%'}}>
        <TextField value={this.state.calorimeter[field]} style={{width: '100%'}}
                   onChange={this.onFieldChange.bind(null, field)}
                   floatingLabelText={floatingLabel}
                   floatingLabelFixed={fixedLabel} />
        <p className="text-muted" style={{fontSize: '90%'}}>{fixedLabel}</p>
      </div>
    )
  }

  render() {
    const renderTextField = this.renderTextField;
    return (
      <Card>
        <CardText>
          <h3>PID Controller Paramters</h3>
          {renderTextField('K_p', 'Proportionality Factor')}
          <br/>
          {renderTextField('K_i', 'Integral Factor')}
          <br/>
          {renderTextField('K_d', 'Derivative Factor')}
          <br/><br/>

          <h3>Temperature Stabilization</h3>
          {renderTextField('max_ramp_rate', 'Linear ramp rate max.', 'The maximum step size when the temperature set point is incremented.')}
          <br/>
          {renderTextField('temp_tolerance_range', 'Temperature comparison tolerance')}
          <p className="text-muted">Temperature values within {this.state.calorimeter.temp_tolerance_range} &deg;C
            will be considered 'equal' for purposes of comparison.</p>
          <br/>
          {renderTextField('temp_tolerance_duration', 'Temperature stabilisation duration',
            'Time duration in seconds, in which temperature is held constant and considered to be "stable".')}
          <br/>


          <h3>Device Refresh Intervals</h3>
          <p>
            The interval entered here is a minimum value.
            Certain actions may take longer than the time duration specified and delay each cycle.
            Unit: seconds.
          </p>
          {renderTextField('idle_loop_interval',
            'Idle Refresh Interval',
            'The refresh interval controls the frequency at which the device connects to the web.')}
          <br/>
          {renderTextField('active_loop_interval',
            'Active Refresh Interval',
            'The refresh interval controls the frequency at which the device uploads data to this website and the PID calculation refresh rate.')}
          <br/><br/>

          <h3>Minimum Upload Batch</h3>
          <p>To prevent making too many HTTP requests, the device uploads measurements in batches. This value changes the minimum number of measurements in each batch.</p>
          {renderTextField('web_api_min_upload_length',
            'Minimum Upload Batch',
            'To prevent making too many HTTP requests, the device uploads measurements in batches. This value changes the minimum number of measurements in each batch.')}
          <br/><br/>

          <p className="text-right text-muted">Changes will not affect any jobs currently running.</p>
          <div className="text-right">
            <FlatButton label="Reset" onTouchTap={() => this.setState({calorimeter: this.props.calorimeter})}/>
            <RaisedButton label="Submit" primary onTouchTap={this.submit} />
          </div>
        </CardText>
      </Card>
    )
  }
}