package org.venice.beachfront.bfapi.model;

import org.junit.Assert;
import org.junit.Test;

import static org.junit.Assert.*;

public class JobStatusTest {

    @Test
    public void getJobId() {
        JobStatus status1 = new JobStatus();
        JobStatus status2 = new JobStatus();

        status2.setJobId(status1.getJobId());
        status2.setStatus(status1.getStatus());

        Assert.assertEquals(status1.getJobId(), status2.getJobId());
        Assert.assertEquals(status1.getStatus(), status2.getStatus());
    }
}