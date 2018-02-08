package org.venice.beachfront.bfapi.model;

import java.sql.Timestamp;
import javax.persistence.AttributeConverter;
import javax.persistence.Converter;

import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.venice.beachfront.bfapi.database.dao.JobDao;
import org.venice.beachfront.bfapi.services.JobService;

@Converter
public class JobConverter implements AttributeConverter<Job, String> {
    @Autowired
    JobService jobDao;

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
         System.out.println("Job Dao: " + jobDao);
         return jobDao.getJob(jobId);
    }
}
