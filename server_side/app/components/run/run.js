import React, {Component} from 'react';
import moment from 'moment';
import axios from 'axios';
import isEmpty from 'lodash/isEmpty';
import last from 'lodash/last';
import concat from 'lodash/concat';

import {Card, CardActions, CardTitle, CardText} from 'material-ui/Card';
import TrendingUp from 'material-ui/svg-icons/action/trending-up';
import FastForward from 'material-ui/svg-icons/AV/fast-forward';
import Hourglass from 'material-ui/svg-icons/action/hourglass-empty';
import Email from 'material-ui/svg-icons/communication/email';
import Time from 'material-ui/svg-icons/device/access-time';
import Divider from 'material-ui/Divider';
import Paper from 'material-ui/Paper';
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
    };
    this.refresh = this.refresh.bind(this);
    this.onExpandChange = this.onExpandChange.bind(this);
    this.renderStats = this.renderStats.bind(this);
    this.renderDetails = this.renderDetails.bind(this);
  }

  normalize(data_points) {
    const sorted = data_points.sort((prev, next) => {
      return new Date(prev.measured_at) - new Date(next.measured_at)
    });
    const oldest_point = sorted[0];
    var result = sorted.map((value, index) => {
      const new_value = value;
      new_value.time_since = Math.abs(moment(value.measured_at).diff(oldest_point.measured_at, 'seconds'));
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
        console.log(response.data);
        const concatenated = concat(data_points, response.data);
        this.setState({data_points: this.normalize(concatenated)});
        toggleLoading();
      })
      .catch((error) => {
        toggleLoading();
      })
  }
  componentDidMount() {
    if(this.state.expanded) {
      this.refresh();
    }
  }
  onExpandChange(expanded) {
    this.setState({expanded});
    if(expanded) {
      this.refresh();
    }
  }

  renderStats() {
    const {run} = this.props;
    return (
      <div>
        <h4>REAL-TIME STATS</h4>
        <RunOptions run={run} />
      </div>
    )
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
    const { expanded, data_points } = this.state;
    const { id, name, is_running, is_finished } = run;
    const active = is_running || !is_finished;
    const cardTitleText = !!name ? name : `Run #${id}`;
    const cardSubtitleText = is_running
      ? 'Currently running...'
      : is_finished ? 'Finished' : 'Waiting for cells to reach starting temperature...';

    return (
      <Card expanded={expanded} onExpandChange={this.onExpandChange} zDepth={1} style={{marginBottom: '1em'}}>
        <CardTitle title={cardTitleText} subtitle={cardSubtitleText}
                   actAsExpander showExpandableButton />
        <CardText style={{marginTop: '-1em', marginBottom: '0'}}>
          {active ? this.renderStats() : this.renderDetails()}
        </CardText>
        <Divider />
        <CardText expandable>
          {data_points.length > 0 && <PlotContainer data_points={data_points} run={run} />}
        </CardText>
        <Divider />
        <CardText expandable>
          {active ? this.renderDetails() : this.renderStats()}
        </CardText>
      </Card>
    )
  }
}