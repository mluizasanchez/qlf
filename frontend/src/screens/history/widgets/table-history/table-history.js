import React, { Component } from 'react';
import { Table, TableBody } from 'material-ui/Table';
import PropTypes from 'prop-types';
import HistoryHeader from './history-header/history-header';
import HistoryData from './history-data/history-data';
import _ from 'lodash';

export default class TableHistory extends Component {
  static propTypes = {
    getHistory: PropTypes.func.isRequired,
    rows: PropTypes.array.isRequired,
    navigateToQA: PropTypes.func.isRequired,
    onRowSelection: PropTypes.func,
    type: PropTypes.string.isRequired,
    selectable: PropTypes.bool,
    orderable: PropTypes.bool,
    processId: PropTypes.number,
    lastProcessedId: PropTypes.number,
    selectedExposures: PropTypes.array,
    rowsCount: PropTypes.number,
    startDate: PropTypes.string,
    endDate: PropTypes.string,
  };

  state = {
    asc: undefined,
    ordering: '-pk',
    offset: 0,
  };

  componentWillReceiveProps(nextProps) {
    if (
      nextProps.startDate &&
      nextProps.endDate &&
      this.props.endDate !== nextProps.endDate
    ) {
      this.props.getHistory(
        nextProps.startDate,
        nextProps.endDate,
        this.state.ordering,
        this.state.offset
      );
    }
  }

  getHistory = async ordering => {
    const order = this.state.asc ? ordering : `-${ordering}`;
    this.props.getHistory(
      this.props.startDate,
      this.props.endDate,
      order,
      this.state.offset
    );
    this.setState({
      asc: !this.state.asc,
      ordering,
    });
  };

  selectProcessQA = pk => {
    this.props.navigateToQA(pk);
  };

  renderBody = () => {
    const isProcessHistory = this.props.type === 'process';
    return (
      <TableBody
        showRowHover={true}
        displayRowCheckbox={!isProcessHistory && this.props.selectable}
      >
        {this.props.rows.map((row, id) => {
          const processId =
            isProcessHistory || !row.last_exposure_process_id
              ? row.pk
              : row.last_exposure_process_id;
          return (
            <HistoryData
              key={id}
              processId={processId}
              row={row}
              selectProcessQA={this.selectProcessQA}
              type={this.props.type}
              lastProcessedId={this.props.lastProcessedId}
              selectedExposures={this.props.selectedExposures}
            />
          );
        })}
      </TableBody>
    );
  };

  nextPage = async page => {
    this.props.getHistory(
      this.props.startDate,
      this.props.endDate,
      this.state.ordering,
      page * 10
    );
  };

  renderPagination = () => {
    if (!this.props.rowsCount) return;
    const pages = Math.floor(this.props.rowsCount / 10) + 1;
    return (
      <div>
        {_.range(pages).map((page, id) => {
          return (
            <span key={id} onClick={() => this.nextPage(page)}>
              {page + 1}{' '}
            </span>
          );
        })}
      </div>
    );
  };

  render() {
    const isProcessHistory = this.props.type === 'process';
    return (
      <div>
        <Table
          fixedHeader={false}
          style={{ width: 'auto', tableLayout: 'auto' }}
          bodyStyle={{ overflow: 'visible' }}
          selectable={!isProcessHistory && this.props.selectable}
          multiSelectable={true}
          onRowSelection={this.props.onRowSelection}
        >
          <HistoryHeader
            getHistory={this.getHistory}
            type={this.props.type}
            asc={this.state.asc}
            ordering={this.state.ordering}
            selectable={this.props.selectable}
            orderable={this.props.orderable}
          />
          {this.renderBody()}
        </Table>
        {this.renderPagination()}
      </div>
    );
  }
}
