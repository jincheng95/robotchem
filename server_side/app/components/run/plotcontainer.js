import React, {Component} from "react";
import moment from "moment";
import includes from "lodash/includes";
import concat from "lodash/concat";
import Divider from "material-ui/Divider";
import LinePlot from "./lineplot";
import PlotToolbar from "./plottoolbar";
import {ReferenceLine} from "recharts";

export default class PlotContainer extends Component {
  constructor(props) {
    super(props);
    this.state = {
      plots: [
        {
          type: 'line',
          xKey: 'time_since',
          yKeys: ['temp_ref', 'temp_sample',]
        },
      ],
      new_plot: {
        type: 'line',
        xKey: 'temp_sample',
        yKeys: ['heat_diff'],
      },
    };
    this.getReferenceLines = this.getReferenceLines.bind(this);
    this.handlePlotChange = this.handlePlotChange.bind(this);
    this.handleNewPlotChange = this.handleNewPlotChange.bind(this);
    this.renderIndividualPlot = this.renderIndividualPlot.bind(this);
    this.handleAddPlot = this.handleAddPlot.bind(this);
    this.handleDeletePlot = this.handleDeletePlot.bind(this);
  }

  getReferenceLines(xKey, yKeys) {
    const {run, data_points} = this.props;
    const {start_temp, target_temp, is_finished} = run;

    var refs = [];
    if( includes(yKeys, 'temp_ref') || includes(yKeys, 'temp_sample') ){
      refs = concat(refs, [
        (<ReferenceLine key="start-temp" alwaysShow y={start_temp} label="Start" stroke="red" strokeDasharray="5 5"/>),
        (<ReferenceLine key="target-temp" alwaysShow y={target_temp} label="End" stroke="red" strokeDasharray="5 5"/>),
      ]);
    }

    if ( xKey == 'time_since' && !is_finished ) {
      const diff = moment().diff(data_points[0].measured_at, 'seconds');
      refs = concat(refs,
        (<ReferenceLine key="now-relative" x={diff} label="Now" stroke="grey" strokeDasharray="3 3"/>)
      );
    }
    if ( xKey == 'time_of_day' && !is_finished ) {
      const now = moment().unix();
      refs = concat(refs,
        (<ReferenceLine key="now-absolute" x={now} label="Now" stroke="grey" strokeDasharray="3 3"/>)
      );
    }
    return refs;
  }

  handlePlotChange(plotIndex, key, value) {
    const { plots } = this.state;
    const plot = plots[plotIndex];
    plots[plotIndex] = {...plot};
    plots[plotIndex][key] = value;
    this.setState({plots});
  }
  handleNewPlotChange(key, value) {
    const { new_plot } = this.state;
    var _new_plot = {...new_plot};
    _new_plot[key] = value;
    this.setState({new_plot: _new_plot});
  }
  handleAddPlot() {
    const { plots, new_plot } = this.state;
    const concatenated = concat(plots, new_plot);
    this.setState({
      plots: concatenated,
      new_plot: {
        type: 'line',
        xKey: 'temp_sample',
        yKeys: ['heat_diff',],
      },
    });
  }
  handleDeletePlot(plotIndex) {
    const { plots } = this.state;
    plots.splice(plotIndex, 1);
    this.setState({plots});
  }

  renderIndividualPlot(type, index, extraProps) {
    const props = {
      data: this.props.data_points,
      key: index,
      ...extraProps,
    };
    switch (type) {
      case "line":
        return React.cloneElement(<LinePlot />, props);
        break;
      default:
        return React.cloneElement(<LinePlot />, props);
    }
  }

  render() {
    const { plots, new_plot } = this.state;
    var title = this.props.is_active ? "Real Time Plot" : "Plot";
    return (
      <div>
        {plots.map((value, index) => {
          const displayedTitle = plots.length == 1 ? title : `${title} ${index+1}`;
          return (
            <div key={index}>
              <h4>{displayedTitle}</h4>

              {<PlotToolbar plot={value}
                            canDelete={plots.length !== 1} handleDeletePlot={this.handleDeletePlot.bind(null, index)}
                            handlePlotChange={this.handlePlotChange.bind(null, index)}/>}

              {this.renderIndividualPlot(
                value.type,
                index,
                {referenceLines: this.getReferenceLines(value.xKey, value.yKeys), ...value}
              )}

              {(index+1) != plots.length && <Divider />}
            </div>
          )
        })}
        <hr style={{margin: '1em 0.1em'}}/>
        <div key="new">
          <h4>ADD NEW PLOT</h4>
          {plots.length > 2 &&
          <p className="text-primary">Due to the amount of data, having more plots may impact your performance negatively.</p>}
          <PlotToolbar plot={new_plot}
                       handlePlotChange={this.handleNewPlotChange}
                       noMargin strongBackground
                       canDelete={false}
                       canAdd handleAddPlot={this.handleAddPlot} />
        </div>
      </div>
    )
  }
}