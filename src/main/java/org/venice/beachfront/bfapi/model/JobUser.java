/**
 * Copyright 2018, Radiant Solutions, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 **/
package org.venice.beachfront.bfapi.model;

import java.io.Serializable;
import java.util.Objects;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.IdClass;
import javax.persistence.JoinColumn;
import javax.persistence.OneToOne;
import javax.persistence.Table;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.hibernate.annotations.OnDelete;
import org.hibernate.annotations.OnDeleteAction;

@Entity
@IdClass(JobUser.JobUserPK.class)
@Table(name = "__beachfront__job_user")
public class JobUser {
	@Id
	@JoinColumn(name = "job_id", nullable = false, columnDefinition = "VARCHAR(64)")
	@OnDelete(action = OnDeleteAction.CASCADE)
	@OneToOne
	@JsonProperty("job_id")
	private Job job;
	@Id
	@JoinColumn(name = "user_id", nullable = false, columnDefinition = "VARCHAR(255)")
	@OnDelete(action = OnDeleteAction.CASCADE)
	@OneToOne
	@JsonProperty("user_id")
	private UserProfile user;

	public JobUser() {
		super();
	}

	public JobUser(Job job, UserProfile user) {
		this.job = job;
		this.user = user;
	}

	class JobUserPK implements Serializable {
		protected Job job;
		protected UserProfile user;

		public JobUserPK() { super(); }

		public JobUserPK(Job job, UserProfile user) {
			this.job = job;
			this.user = user;
		}

		public Job getJob() {
			return job;
		}

		public void setJob(Job job) {
			this.job = job;
		}

		public UserProfile getUser() {
			return user;
		}

		public void setUser(UserProfile user) {
			this.user = user;
		}

		@Override
		public boolean equals(Object o) {
			if (this == o) return true;
			if (o == null || getClass() != o.getClass()) return false;
			JobUserPK jobUserPK = (JobUserPK) o;
			return job.getJobId().equals(jobUserPK.job.getJobId()) &&
					user.getUserId().equals(jobUserPK.user.getUserId());
		}

		@Override
		public int hashCode() {
			return Objects.hash(job.getJobId(), user.getUserId());
		}
	}

	public Job getJob() {
		return job;
	}

	public void setJob(final Job job) {
		this.job = job;
	}

	public UserProfile getUser() {
		return user;
	}

	public void setUser(final UserProfile user) {
		this.user = user;
	}
}
