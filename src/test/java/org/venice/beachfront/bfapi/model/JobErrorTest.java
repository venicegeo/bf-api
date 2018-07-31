package org.venice.beachfront.bfapi.model;

import org.junit.Assert;
import org.junit.Test;

import static org.junit.Assert.*;

public class JobErrorTest {

    @Test
    public void testGettersAndSetters() {
        Job job = new Job();
        job.setJobId("my_job_id");

        JobErrorPK pk1 = new JobErrorPK();
        pk1.setJob(job);
        JobErrorPK pk2 = new JobErrorPK(job);

        Assert.assertTrue(pk1.equals(pk2));

        String errorMsg = "the_error_message";
        String executionStep = "the_execution_step";

        JobError jobError1 = new JobError();
        jobError1.setErrorMessage(errorMsg);
        jobError1.setExecutionStep(executionStep);
        jobError1.setJob(pk1);

        JobError jobError2 = new JobError(job, errorMsg, executionStep);

        Assert.assertTrue(jobError1.equals(jobError2));

        Assert.assertEquals(jobError1.getErrorMessage(), jobError2.getErrorMessage());
        Assert.assertEquals(jobError1.getExecutionStep(), jobError2.getExecutionStep());
        Assert.assertEquals(jobError1.hashCode(), jobError2.hashCode());
        Assert.assertEquals(jobError1.toString(), jobError2.toString());

    }

}