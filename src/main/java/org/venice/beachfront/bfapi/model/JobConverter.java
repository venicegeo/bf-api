package org.venice.beachfront.bfapi.model;

import javax.persistence.AttributeConverter;
import javax.persistence.Converter;

import org.springframework.beans.factory.annotation.Autowired;
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
