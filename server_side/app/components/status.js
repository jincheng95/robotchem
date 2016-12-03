import React, {Component} from 'react';

export default class Status extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    console.log(this.props);
    const { calorimeter } = this.props;
    const { name, serial, last_comm_time, current_ref_temp, current_sample_temp } = calorimeter;
    return (
      <div>
        <div className="col-sm-12 col-md-6 col-lg-5">
          <span>
            <h1>
              {name}
            </h1>
            <p className="text-muted">
              Serial Number: {serial}
            </p>
          </span>
        </div>

        <div className="col-sm-12 col-md-6 col-lg-7">

        </div>
        <hr/>
      </div>
    )
  }
}