import React, {Component} from 'react';
import forEach from 'lodash/forEach';
import xor from 'lodash/xor';
import keys from 'lodash/keys';
import take from 'lodash/take';

import NoteAdd from 'material-ui/svg-icons/action/note-add';
import Delete from 'material-ui/svg-icons/action/delete';
import MenuItem from 'material-ui/MenuItem';
import DropDownMenu from 'material-ui/DropDownMenu';
import RaisedButton from 'material-ui/RaisedButton';
import Flatbutton from 'material-ui/FlatButton';
import Divider from 'material-ui/Divider';
import {Toolbar, ToolbarGroup, ToolbarSeparator, ToolbarTitle} from 'material-ui/Toolbar';

import humanized_axes, {simple_humanized_axes} from '../../utils/humanize_axes';

export default class PlotToolbar extends Component {
	constructor(props) {
		super(props);
    this.handleXKeyChange = this.handleXKeyChange.bind(this);
    this.handleYKeyChange = this.handleYKeyChange.bind(this);
    this.handleAddYKey = this.handleAddYKey.bind(this);
    this.handleRemoveYKey = this.handleRemoveYKey.bind(this);
	}


	handleXKeyChange (event, index, value) {
    this.props.handlePlotChange('xKey', value);
  }
  handleYKeyChange (yKeyIndex, event, valueIndex, value) {
    if(value === '-'){
      this.handleRemoveYKey(yKeyIndex);
    } else {
      const {yKeys} = this.props.plot;
      yKeys[yKeyIndex] = value;
      this.props.handlePlotChange('yKeys', yKeys);
    }

  }
  handleAddYKey() {
    const {yKeys, xKey} = this.props.plot;
    var unusedKeys = xor(yKeys, keys(humanized_axes));
    yKeys.unshift(unusedKeys[0]);
    this.props.handlePlotChange('yKeys', yKeys);
  }
  handleRemoveYKey(indexToRemove) {
    const {yKeys} = this.props.plot;
    yKeys.splice(indexToRemove, 1);
    this.props.handlePlotChange('yKeys', yKeys);
  }

	render() {
		const {plot, noMargin, strongBackground, canDelete, canAdd, handleAddPlot, handleDeletePlot} = this.props;
		const {type, xKey, yKeys} = plot;

    // Styles
    const dropDownStyle = {
      padding: '3px', margin: '8px -20px -8px -20px',
    };
    const toolbarStyle= {
      backgroundColor: strongBackground ? 'rgba(222, 222, 222, 0.5)' : 'rgba(222, 222, 222, 0.1)',
      marginLeft: noMargin ? null : '2em', marginBottom: '0.2em',
      borderBottom:  '1px solid rgba(200, 200, 200, 0.2)',
      borderTop: '1px solid rgba(200, 200, 200, 0.2)',
    };
    const labelStyle = {
      fontSize: `${100-yKeys.length * 7.5}%`,
      overflow: 'ellipsis',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
    };
    const underlineStyle ={
      borderTop: '1px solid rgba(0, 0, 0, 0.9)',
    };
    const iconStyle = {
      fill: 'rgba(0, 0, 0, 0.96)',
    };
    const dropDownProps = {
      style: dropDownStyle,
      underlineStyle,
      iconStyle,
    };

    var axisMenuItems = [];
    forEach(humanized_axes, (value, key) => {
      const label = (
        <p style={labelStyle}>
          {simple_humanized_axes[key]}
        </p>
      );
      axisMenuItems.push(
        <MenuItem key={key}
                  value={key} label={label} primaryText={value}/>
      );
    });

		return (
		  <Toolbar style={toolbarStyle}>
        <ToolbarGroup key="y" firstChild={true}>
          {yKeys.length < 5 && <Flatbutton label="Add Series" primary onClick={this.handleAddYKey}/>}
          {yKeys.map((key, index) => {
            return (
              <div key={index}>
                <DropDownMenu value={key} onChange={this.handleYKeyChange.bind(null, index)} key={index}
                              {...dropDownProps}>
                  {axisMenuItems}
                  <Divider />
                  <MenuItem key="remove" value='-'
                            label="Remove this series" primaryText="Remove this series" />
                </DropDownMenu>
              </div>
            )
          })}
        </ToolbarGroup>

        <ToolbarGroup>
          <ToolbarTitle text="against" style={{fontSize: '125%'}}/>
        </ToolbarGroup>

        <ToolbarGroup key="x" >
          <div>
            <DropDownMenu value={xKey} onChange={this.handleXKeyChange} key="1"
                          {...dropDownProps}>
              {axisMenuItems}
            </DropDownMenu>
          </div>
        </ToolbarGroup>

        {(canDelete || canAdd) &&
        <ToolbarGroup key="plot" lastChild={true}>
          <ToolbarSeparator/>
          {canDelete && <RaisedButton icon={<Delete />} secondary onClick={handleDeletePlot}/>}
          {canAdd && <RaisedButton icon={<NoteAdd />} primary onClick={handleAddPlot}/>}
        </ToolbarGroup>}
      </Toolbar>
		)
	}
}