import React, { Component } from 'react';
import PropTypes from 'prop-types';
import TableHistory from './widgets/table-history/table-history';
import SelectDate from './widgets/select-date/select-date';
import Tab from 'material-ui/Tabs';
import Tabs from 'material-ui/Tabs';
import Card from 'material-ui/Card';
import { Toolbar, ToolbarGroup, ToolbarSeparator } from 'material-ui/Toolbar';
import Icon from 'material-ui/Icon';
import Dialog from 'material-ui/Dialog';
import Button from 'material-ui/Button';
import QlfApi from '../../containers/offline/connection/qlf-api';
import _ from 'lodash';
import { withStyles } from 'material-ui/styles';
import AppBar from 'material-ui/AppBar';

const styles = {
  appBar: {},
  root: {},
  tabs: {},
  card: {
    borderLeft: 'solid 4px teal',
    flex: '1',
    height: '90%',
    margin: '1em',
  },
};

class History extends Component {
  static propTypes = {
    getHistory: PropTypes.func.isRequired,
    navigateToQA: PropTypes.func.isRequired,
    rows: PropTypes.array.isRequired,
    startDate: PropTypes.string,
    endDate: PropTypes.string,
    lastProcesses: PropTypes.array,
    type: PropTypes.string.isRequired,
    lastProcessedId: PropTypes.number,
    rowsCount: PropTypes.number,
    classes: PropTypes.object,
  };

  renderSelectDate = () => {
    if (this.props.startDate && this.props.endDate)
      return (
        <SelectDate
          startDate={this.props.startDate}
          endDate={this.props.endDate}
          setHistoryRangeDate={this.setHistoryRangeDate}
        />
      );
  };

  setHistoryRangeDate = (startDate, endDate) => {
    this.setState({ startDate, endDate });
  };

  state = {
    tab: 'history',
    confirmDialog: false,
    selectedExposures: [],
    startDate: this.props.startDate,
    endDate: this.props.endDate,
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.startDate && nextProps.endDate) {
      this.setState({
        startDate: nextProps.startDate,
        endDate: nextProps.endDate,
      });
    }
  }

  renderLastProcesses = () => {
    let lastProcesses = this.props.lastProcesses
      ? this.props.lastProcesses
      : [];
    if (this.props.type === 'exposure')
      lastProcesses = _.uniq(lastProcesses.map(lp => lp.exposure_id)).map(exp =>
        _.maxBy(lastProcesses.filter(lp => lp.exposure_id === exp), 'pk')
      );
    return (
      <TableHistory
        getHistory={this.props.getHistory}
        rows={lastProcesses}
        navigateToQA={this.props.navigateToQA}
        type={this.props.type}
        selectable={false}
        orderable={false}
        startDate={this.state.startDate}
        endDate={this.state.endDate}
        lastProcessedId={this.props.lastProcessedId}
        rowsCount={this.props.rowsCount}
      />
    );
  };

  onRowSelection = rows => {
    if (rows === 'all') {
      const selectedExposures = this.props.rows.map((row, id) => id);
      this.setState({ selectedExposures });
      return;
    }

    if (rows === 'none') {
      this.setState({ selectedExposures: [] });
      return;
    }

    const selectedExposures = this.state.selectedExposures.includes(rows[0])
      ? this.state.selectedExposures.filter(row => !rows.includes(row))
      : this.state.selectedExposures.concat(rows);
    this.setState({ selectedExposures });
  };

  renderRows = () => {
    if (this.props.rows) {
      return (
        <TableHistory
          getHistory={this.props.getHistory}
          startDate={this.state.startDate}
          endDate={this.state.endDate}
          rows={this.props.rows}
          navigateToQA={this.props.navigateToQA}
          type={this.props.type}
          selectable={true}
          orderable={true}
          lastProcessedId={this.props.lastProcessedId}
          onRowSelection={this.onRowSelection}
          selectedExposures={this.state.selectedExposures}
          rowsCount={this.props.rowsCount}
        />
      );
    }
  };

  renderToolbar = () => {
    return (
      <Toolbar>
        <ToolbarGroup firstChild={true}>
          <Icon
            className="material-icons"
            title="Clear QA"
            onClick={() => this.props.navigateToQA(0)}
          >
            clear_all
          </Icon>
          <Icon
            className="material-icons"
            title="Refresh"
            onClick={() =>
              this.props.getHistory(
                this.props.startDate,
                this.props.endDate,
                '-pk',
                0
              )
            }
          >
            refresh
          </Icon>
          {this.renderSelectDate()}
        </ToolbarGroup>
        {this.renderReprocessButton()}
      </Toolbar>
    );
  };

  reprocessExposure = () => {
    const exposures = this.state.selectedExposures.map(
      exposure => this.props.rows[exposure].exposure_id
    );
    exposures.forEach(async exp => {
      await QlfApi.reprocessExposure(exp);
    });
    this.setState({ confirmDialog: false });
  };

  renderReprocessButton = () => {
    if (this.state.selectedExposures.length < 1) return;
    return (
      <ToolbarGroup>
        <ToolbarSeparator />
        <Icon
          className="material-icons"
          title="Replay"
          onClick={this.handleOpenDialog}
        >
          replay
        </Icon>
      </ToolbarGroup>
    );
  };

  handleOpenDialog = () => {
    this.setState({ confirmDialog: true });
  };

  handleCloseDialog = () => {
    this.setState({ confirmDialog: false });
  };

  exposuresToReprocess = () => {
    const exposures = this.state.selectedExposures
      .map(row => this.props.rows[row].exposure_id)
      .join(', ');
    return `exposure${exposures.length > 1 ? 's' : ''} ${exposures}`;
  };

  render() {
    const actions = [
      <Button
        key={0}
        label="Cancel"
        primary={true}
        onClick={this.handleCloseDialog}
      />,
      <Button
        key={1}
        label="Submit"
        primary={true}
        onClick={this.reprocessExposure}
      />,
    ];
    console.log(this.props.classes);

    return (
      <div
        className={this.props.classes.root}
        style={{ WebkitAppRegion: 'no-drag' }}
      >
        <Dialog
          actions={actions}
          modal={false}
          open={this.state.confirmDialog}
          onRequestClose={this.handleClose}
        >
          Reprocess {this.exposuresToReprocess()}?
        </Dialog>
        <Card className={this.props.classes.card} style={styles.card}>
          <AppBar className={this.props.classes.appBar} position="static">
            <Tabs
              className={this.props.classes.tabs}
              value={this.state.value}
              onChange={this.handleChange}
            >
              <Tab label="Most Recent" value="last" />
              <Tab label="History" value="history" />
            </Tabs>
          </AppBar>
          {this.state.value === 'last' && this.renderLastProcesses()}
          {this.state.value === 'history' && this.renderRows()}
        </Card>
      </div>
    );
  }
}

export default withStyles(styles)(History);
