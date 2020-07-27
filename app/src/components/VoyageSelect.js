import React, { Component } from 'react';

import { Select, MenuItem } from '@material-ui/core';


export default class VoyageSelect extends Component {
    constructor(props) {
        super(props);
        this.onVoyageChange = this.onVoyageChange.bind(this)
    }

    onVoyageChange(event, value) {
        this.props.voyageUpdate(value.props.value);
    }

    render() {

        const {
            AllText = (this.props.selectedVoyage === -1) ? 'Select a voyage' : 'View all voyages',
        } = this.props;

        return (
            <div id="voyage-select">
                <Select value={this.props.selectedVoyage} onChange={this.onVoyageChange}>
                    <MenuItem key={-1} value={-1}>{AllText}</MenuItem>
                    {this.props.voyageMetadata.map((metadata, voyage_id) =>
                        <MenuItem key={voyage_id} value={voyage_id}>{metadata.vesselName} {metadata.year_from}-{metadata.year_to}</MenuItem>
                    )}
                </Select>
            </div>
        );
    }
}