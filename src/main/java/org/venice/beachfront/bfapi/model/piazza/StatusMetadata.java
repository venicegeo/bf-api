package org.venice.beachfront.bfapi.model.piazza;

import org.venice.beachfront.bfapi.model.Job;

/**
 * Holds the Job Status metadata for a Piazza job. If incomplete, Piazza will only return the status. However, if a Job
 * is complete (or failed) the Piazza response will also contain either the Data ID of the shoreline detection (if
 * succeeded), and the error detail message (if failed)
 */
public class StatusMetadata {
	private String status;
	private String dataId;
	private String errorMessage;

	public StatusMetadata() {

	}

	public StatusMetadata(String status) {
		this.status = status;
	}

	public String getStatus() {
		return status;
	}

	public void setStatus(String status) {
		this.status = status;
	}

	public String getDataId() {
		return dataId;
	}

	public void setDataId(String dataId) {
		this.dataId = dataId;
	}

	public String getErrorMessage() {
		return errorMessage;
	}

	public void setErrorMessage(String errorMessage) {
		this.errorMessage = errorMessage;
	}

	/**
	 * Returns true if the Status is in an error state
	 */
	public boolean isStatusError() {
		return Job.STATUS_CANCELLED.equals(status) || Job.STATUS_ERROR.equals(status) || Job.STATUS_FAIL.equals(status);
	}

	/**
	 * Returns true if the Status is in a successful state
	 */
	public boolean isStatusSuccess() {
		return Job.STATUS_SUCCESS.equals(status);
	}

	/**
	 * Returns true if the Status is in an incomplete state
	 */
	public boolean isStatusIncomplete() {
		return Job.STATUS_PENDING.equals(status) || Job.STATUS_RUNNING.equals(status) || Job.STATUS_SUBMITTED.equals(status);
	}
}
