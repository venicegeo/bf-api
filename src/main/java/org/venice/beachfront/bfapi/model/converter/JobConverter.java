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
package org.venice.beachfront.bfapi.model.converter;

import javax.persistence.AttributeConverter;
import javax.persistence.Converter;

import org.springframework.beans.factory.annotation.Autowired;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.services.JobService;

@Converter(autoApply = true)
public class JobConverter implements AttributeConverter<Job, String>, org.springframework.core.convert.converter.Converter<String, Job> {
    @Autowired
    JobService jobService;

    @Override
    public String convertToDatabaseColumn(Job job) {
         if (job == null) {
            return null;
         }
         return job.getJobId();
    }

    @Override
    public Job convertToEntityAttribute(String jobId) {
         if (jobId == null) {
            return null;
         }
         System.out.println("Job Dao: " + jobService);
         return jobService.getJob(jobId);
    }

    @Override
    public Job convert(String jobId) {
        return convertToEntityAttribute(jobId);
    }
}
