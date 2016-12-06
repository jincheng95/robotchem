import React, {Component} from 'react';
import moment from 'moment';
import axios from 'axios';
import isEmpty from 'lodash/isEmpty';
import last from 'lodash/last';
import concat from 'lodash/concat';

import {Card, CardActions, CardTitle, CardText} from 'material-ui/Card';
import Divider from 'material-ui/Divider';
import RaisedButton from 'material-ui/RaisedButton';
import FlatButton from 'material-ui/FlatButton';
import Dialog from 'material-ui/Dialog';
import RefreshIndicator from 'material-ui/RefreshIndicator';

import Stop from 'material-ui/svg-icons/AV/stop';
import CloudDownload from 'material-ui/svg-icons/file/cloud-download';
import TrendingUp from 'material-ui/svg-icons/action/trending-up';
import FastForward from 'material-ui/svg-icons/AV/fast-forward';
import Hourglass from 'material-ui/svg-icons/action/hourglass-empty';
import Email from 'material-ui/svg-icons/communication/email';
import Time from 'material-ui/svg-icons/device/access-time';
import {red500} from 'material-ui/styles/colors';

import {Grid, Row, Col} from 'react-flexbox-grid';

import PlotContainer from './plotcontainer';


const StatColumn = (props) => {
  const { icon, text } = props;
  const fixedIcon = React.cloneElement(icon, {
    style: {
      width: '19px',
      height: '19px',
      color: 'grey',
      marginRight: '4px',
    }
  });
  return (
    <span>
      {fixedIcon}
      {text}
      <br/>
    </span>
  )
};

const RunOptions = (props) => {
  const { id, name, creation_time, start_time, is_running, is_finished,
        start_temp, target_temp, ramp_rate, calorimeter, email } = props.run;
  const duration = is_running ? `Started ${moment().diff(moment(start_time))} ago` : 'Waiting...';
  return (
    <div className="row">
      <div className="col-xs-6 col-sm-6 col-md-5 col-lg-5 col-md-offset-1 col-lg-offset-1">
        <StatColumn icon={<TrendingUp />} text={`From ${start_temp} to ${target_temp} °C`} />
        <StatColumn icon={<FastForward />} text={`At ${ramp_rate * 100}% power`} />
      </div>
      <div className="col-xs-6 col-sm-6 col-md-5 col-lg-5">
        <StatColumn icon={<Hourglass />} text={duration} />
        <StatColumn icon={<Time />} text={`Created ${moment(creation_time).calendar()}`} />
      </div>
      {!!email &&
      <div className="col-xs-12 col-sm-12 col-md-11 col-lg-11 col-md-offset-1 col-lg-offset-1">
        <StatColumn icon={<Email />} text={`Notify ${email} when done`} />
      </div>}
    </div>
  )
};


export default class Run extends Component {
  constructor(props) {
    super(props);
    this.state = {
      expanded: isEmpty(props.expanded) ? !props.run.is_finished : props.expanded,
      data_points: [],
      autorefreshInt: null,
      stopDialogOpen: false
    };
    this.refresh = this.refresh.bind(this);
    this.onExpandChange = this.onExpandChange.bind(this);
    this.renderDetails = this.renderDetails.bind(this);
    this.cancelAutorefresh = this.cancelAutorefresh.bind(this);
    this.stopRun = this.stopRun.bind(this);
  }

  normalize(data_points) {
    const sorted = data_points.sort((prev, next) => {
      return new Date(prev.measured_at) - new Date(next.measured_at)
    });
    const oldest_point = sorted[0];
    var result = sorted.map((value, index) => {
      const new_value = value;
      const measured_at = moment(value.measured_at);
      new_value.time_since = Math.abs(measured_at.diff(oldest_point.measured_at, 'seconds'));
      new_value.time_of_day = measured_at.unix();
      new_value.heat_diff = value.heat_sample - value.heat_ref;
      new_value.temp_average = (value.temp_sample + value.temp_ref) / 2;
      return new_value;
    });
    return result;
  }

  refresh() {
    const {data_points} = this.state;
    const {run, code, toggleLoading} = this.props;

    var since;
    if( !isEmpty(data_points) ) {
      since = last(data_points).measured_at;
    } else {
      since = run.creation_time;
    }

    toggleLoading();
    axios.get(`/api/data/?access_code=${code}&run=${run.id}&since=${since}`)
      .then((response) => {
        const concatenated = concat(data_points, response.data);
        this.setState({ data_points: this.normalize(concatenated) });
        toggleLoading();
      })
      .catch((error) => {
        console.log(error.response);
        toggleLoading();
      })
  }
  cancelAutorefresh() {
    const {autorefreshInt} = this.state;
    window.clearInterval(autorefreshInt);
  }
  componentWillReceiveProps() {
    const {expanded, autorefreshInt} = this.state;
    const {autorefresh} = this.props;
    if( expanded && autorefresh && !autorefreshInt ) {
      this.refresh();
      const int = window.setInterval(this.refresh, 5000);
      this.setState({autorefreshInt: int});
    } else if ( !autorefresh && !!autorefreshInt ) {
      this.cancelAutorefresh();
    }
  }
  componentDidMount() {
    this.componentWillReceiveProps();
  }
  componentWillUnmount() {
    this.cancelAutorefresh();
  }
  onExpandChange(expanded) {
    this.setState({expanded});
    if(expanded) {
      this.refresh();
    }
  }

  stopRun() {
    const {code, toggleLoading, statusRefresh} = this.props;
    toggleLoading();
    axios.delete('/api/status/?access_code='+code)
      .then((response) => {
        toggleLoading();
        statusRefresh();
      })
  }

  renderDetails() {
    const {run} = this.props;
    return (
      <div>
        <h4>DETAILS</h4>
        <RunOptions run={run} />
      </div>
    )
  }
  render() {
    const { run } = this.props;
    const { expanded, data_points, stopDialogOpen } = this.state;
    const { id, name, is_running, is_finished } = run;
    const is_active = is_running || (!is_finished);

    const cardTitleText = !!name ? name : `Run #${id}`;
    const cardSubtitleText = is_running
      ? 'Currently running...'
      : is_finished ? 'Finished' : 'Waiting for cells to reach starting temperature...';

    return (
      <Card expanded={expanded} onExpandChange={this.onExpandChange} zDepth={1} style={{marginBottom: '1em'}}>
        <CardTitle title={cardTitleText} subtitle={cardSubtitleText}
                   actAsExpander={!is_active} showExpandableButton={!is_active} />
        <CardText style={{marginTop: '-1.5em'}}>
          {this.renderDetails()}
        </CardText>
        <CardActions style={{marginBottom: '1em', marginLeft: '0.6em'}}>
          <RaisedButton href={`/download/${id}/?format=csv`} target="_blank"
            label="Download As .csv" icon={<CloudDownload/>}/>
          {is_active &&
          <FlatButton onClick={()=>this.setState({stopDialogOpen: true})}
            backgroundColor={red500} label="Stop" icon={<Stop/>} style={{color: 'white'}} />}
        </CardActions>
        <Divider />
        <CardText expandable>
          {data_points.length > 0
            ? <PlotContainer data_points={data_points} run={run} />
            : <div style={{position: 'relative', height: '75px'}}>
                <RefreshIndicator
                  size={40}
                  left={-20}
                  top={28}
                  status={'loading'}
                  style={{marginLeft: '50%'}}
                />
                <p className="text-muted text-center">
                  Measurements either hasn't been made, or data is still being retrived.
                </p>
              </div>}
        </CardText>

        <Dialog title="Are you sure?" open={stopDialogOpen}
                actions={[
                  <FlatButton label="Cancel" onTouchTap={()=>this.setState({stopDialogOpen: false})}/>,
                  <FlatButton label="Stop" onTouchTap={this.stopRun} secondary keyboardFocused />
                ]}
                onRequestClose={()=>this.setState({stopDialogOpen: false})}>
          Once stopped, this run can never be resumed.
        </Dialog>
      </Card>
    )
  }
}